from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

from drone_eval.model.logs import CaptureRecord, CollisionRecord, FlightRecord
from drone_eval.model.mission import MissionConfig
from drone_eval.model.result import EvalResult
from drone_eval.service.evaluator import Evaluator
from drone_eval.service.file_loader import FileLoader
from drone_eval.service.history_manager import HistoryManager
from drone_eval.service.report_exporter import ReportExporter
from drone_eval.service.validator import Validator
from drone_eval.utils.exceptions import EvaluationError, ExportError, FileLoadError, ValidationError
from drone_eval.utils.logger import get_logger

_log = get_logger(__name__)

ProgressCallback = Callable[[str, str, int], None]


def _resolve_image_path(rec: CaptureRecord, base: Path) -> CaptureRecord:
    p = Path(rec.image_path)
    if not p.is_absolute():
        resolved = str(base / p)
        return CaptureRecord(rec.timestamp, rec.x, rec.y, rec.z,
                             rec.roll, rec.pitch, rec.yaw, resolved)
    return rec


@dataclass
class FileState:
    mission_path: str = ""
    flight_path: str = ""
    capture_path: str = ""
    collision_path: str = ""
    image_folder: str = ""

    def is_ready(self) -> bool:
        return bool(self.mission_path and self.flight_path and
                    self.capture_path and self.collision_path)


@dataclass
class ExportConfig:
    output_dir: str = ""
    save_eval_result_json: bool = True
    save_eval_result_csv: bool = True
    save_eval_detail_csv: bool = True
    save_eval_summary_json: bool = True


@dataclass
class SaveResult:
    saved: list[str] = field(default_factory=list)
    failed: list[tuple[str, str]] = field(default_factory=list)

    @property
    def all_succeeded(self) -> bool:
        return len(self.failed) == 0


class AppController:
    def __init__(self, history_dir: str | Path | None = None) -> None:
        self._file_state = FileState()
        self._mission: Optional[MissionConfig] = None
        self._flight_records: list[FlightRecord] = []
        self._capture_records: list[CaptureRecord] = []
        self._collision_records: list[CollisionRecord] = []
        self._eval_result: Optional[EvalResult] = None
        self._validation_errors: list[str] = []
        self._history_manager: Optional[HistoryManager] = (
            HistoryManager(history_dir) if history_dir else None
        )

    @property
    def file_state(self) -> FileState:
        return self._file_state

    @property
    def mission(self) -> Optional[MissionConfig]:
        return self._mission

    @property
    def eval_result(self) -> Optional[EvalResult]:
        return self._eval_result

    @property
    def validation_errors(self) -> list[str]:
        return list(self._validation_errors)

    @property
    def flight_records(self) -> list[FlightRecord]:
        return self._flight_records

    @property
    def capture_records(self) -> list[CaptureRecord]:
        return self._capture_records

    @property
    def collision_records(self) -> list[CollisionRecord]:
        return self._collision_records

    def set_file(self, field_name: str, path: str) -> None:
        setattr(self._file_state, field_name, path)
        self._mission = None
        self._eval_result = None

    def load_mission_config(self) -> MissionConfig:
        path = self._file_state.mission_path
        if not path:
            raise FileLoadError("", "임무 설정 파일 경로가 지정되지 않았습니다.")
        try:
            self._mission = FileLoader.load_mission_config(path)
            _log.info("Loaded mission config from '%s'", path)
            return self._mission
        except Exception as exc:
            raise FileLoadError(path, str(exc)) from exc

    def run_evaluation(self, progress: ProgressCallback | None = None) -> EvalResult:
        if not self._file_state.is_ready():
            raise EvaluationError("필수 입력 파일이 모두 지정되지 않았습니다.")

        def _progress(stage: str, message: str, pct: int) -> None:
            if progress:
                progress(stage, message, pct)
            _log.debug("[%s] %s (%d%%)", stage, message, pct)

        _progress("파일 로드", "임무 설정 파일 로드 중...", 10)
        try:
            mission = FileLoader.load_mission_config(self._file_state.mission_path)
        except Exception as exc:
            raise FileLoadError(self._file_state.mission_path, str(exc)) from exc

        _progress("파일 로드", "비행 로그 로드 중...", 25)
        try:
            flight_records = FileLoader.load_flight_records(self._file_state.flight_path)
        except Exception as exc:
            raise FileLoadError(self._file_state.flight_path, str(exc)) from exc

        _progress("파일 로드", "촬영 로그 로드 중...", 45)
        try:
            capture_records = FileLoader.load_capture_records(self._file_state.capture_path)
        except Exception as exc:
            raise FileLoadError(self._file_state.capture_path, str(exc)) from exc

        if self._file_state.image_folder:
            image_base = Path(self._file_state.image_folder)
            capture_records = [
                _resolve_image_path(rec, image_base) for rec in capture_records
            ]

        _progress("파일 로드", "충돌 로그 로드 중...", 60)
        try:
            collision_records = FileLoader.load_collision_records(self._file_state.collision_path)
        except Exception as exc:
            raise FileLoadError(self._file_state.collision_path, str(exc)) from exc

        _progress("입력 검증", "데이터 검증 중...", 70)
        errors: list[str] = []
        errors.extend(Validator.validate_mission_config(mission))
        errors.extend(Validator.validate_flight_records(flight_records))
        errors.extend(Validator.validate_capture_records(capture_records))
        errors.extend(Validator.validate_collision_records(collision_records))
        self._validation_errors = errors

        if any("duplicate" in e or "must be" in e for e in errors):
            raise ValidationError(errors)

        _progress("매칭 및 평가", "평가 계산 중...", 85)
        try:
            result = Evaluator.evaluate(mission, flight_records, capture_records, collision_records)
        except Exception as exc:
            raise EvaluationError(str(exc)) from exc

        self._mission = mission
        self._flight_records = flight_records
        self._capture_records = capture_records
        self._collision_records = collision_records
        self._eval_result = result

        _progress("결과 준비", "평가 완료", 100)
        _log.info("Evaluation complete. Score: %.1f", result.final_score)
        return result

    def export_results(self, config: ExportConfig, timestamp: str = "") -> SaveResult:
        if self._eval_result is None:
            raise ExportError([("전체", "평가 결과가 없습니다.")])

        output_dir = Path(config.output_dir)
        saved: list[str] = []
        failed: list[tuple[str, str]] = []

        def _try_save(name: str, fn: Callable) -> None:
            path = output_dir / name
            try:
                fn(self._eval_result, path)
                saved.append(str(path))
            except Exception as exc:
                failed.append((name, str(exc)))
                _log.error("Failed to save '%s': %s", name, exc)

        if config.save_eval_result_json:
            _try_save("eval_result.json", ReportExporter.export_eval_result_json)
        if config.save_eval_result_csv:
            _try_save("eval_result.csv", ReportExporter.export_eval_result_csv)
        if config.save_eval_detail_csv:
            _try_save("eval_detail.csv", ReportExporter.export_eval_detail_csv)
        if config.save_eval_summary_json:
            _try_save("eval_summary.json", ReportExporter.export_eval_summary_json)

        if self._history_manager and timestamp:
            try:
                self._history_manager.save_entry(self._eval_result, timestamp)
            except Exception as exc:
                _log.warning("History save failed: %s", exc)

        return SaveResult(saved=saved, failed=failed)

    def load_history(self):
        if self._history_manager is None:
            return []
        return self._history_manager.load_all()

    def delete_history_entry(self, entry_id: str) -> bool:
        if self._history_manager is None:
            return False
        return self._history_manager.delete_entry(entry_id)

    def clear_history(self) -> None:
        if self._history_manager is not None:
            self._history_manager.clear_all()
