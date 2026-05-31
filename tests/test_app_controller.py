from __future__ import annotations

import json
from pathlib import Path

import pytest

from drone_eval.controller.app_controller import AppController, ExportConfig, FileState
from drone_eval.utils.exceptions import EvaluationError, FileLoadError


def _write_mission(path: Path) -> None:
    mission = {
        "mission_id": "test_mission",
        "allow_position_error": 2.0,
        "allow_yaw_error": 10.0,
        "allow_pitch_error": 10.0,
        "score_policy": {
            "position_penalty_per_meter": 5.0,
            "direction_yaw_penalty_per_degree": 2.0,
            "direction_pitch_penalty_per_degree": 2.0,
            "missing_capture_penalty": 10.0,
            "collision_penalty": 20.0,
            "timeout_penalty": 5.0,
            "position_weight": 1.0,
            "direction_weight": 1.0,
        },
        "targets": [
            {"target_id": "T1", "x": 0.0, "y": 0.0, "z": -10.0,
             "yaw": 90.0, "pitch": -30.0, "time_limit": 60.0},
        ],
    }
    path.write_text(json.dumps(mission), encoding="utf-8")


def _write_flight_log(path: Path) -> None:
    rows = [{"timestamp": 1.0, "x": 0.0, "y": 0.0, "z": -10.0,
             "roll": 0.0, "pitch": -30.0, "yaw": 90.0, "speed": 3.0}]
    path.write_text(json.dumps(rows), encoding="utf-8")


def _write_capture_log(path: Path, img_path: str) -> None:
    rows = [{"timestamp": 5.0, "x": 0.2, "y": 0.1, "z": -10.0,
             "roll": 0.0, "pitch": -29.0, "yaw": 91.0, "image_path": img_path}]
    path.write_text(json.dumps(rows), encoding="utf-8")


def _write_collision_log(path: Path) -> None:
    rows = [{"timestamp": 2.0, "collision": False, "x": 0.0, "y": 0.0, "z": -10.0}]
    path.write_text(json.dumps(rows), encoding="utf-8")


@pytest.fixture
def controller(tmp_path: Path) -> AppController:
    return AppController(history_dir=tmp_path / "history")


@pytest.fixture
def ready_controller(tmp_path: Path) -> AppController:
    img = tmp_path / "cap.png"
    img.write_bytes(b"img")

    mission_path = tmp_path / "mission.json"
    flight_path = tmp_path / "flight.json"
    capture_path = tmp_path / "capture.json"
    collision_path = tmp_path / "collision.json"

    _write_mission(mission_path)
    _write_flight_log(flight_path)
    _write_capture_log(capture_path, str(img))
    _write_collision_log(collision_path)

    ctrl = AppController(history_dir=tmp_path / "history")
    ctrl.set_file("mission_path", str(mission_path))
    ctrl.set_file("flight_path", str(flight_path))
    ctrl.set_file("capture_path", str(capture_path))
    ctrl.set_file("collision_path", str(collision_path))
    return ctrl


class TestFileState:
    def test_initial_state_not_ready(self, controller):
        assert controller.file_state.is_ready() is False

    def test_ready_when_all_required_files_set(self, controller):
        controller.set_file("mission_path", "a.json")
        controller.set_file("flight_path", "b.json")
        controller.set_file("capture_path", "c.json")
        controller.set_file("collision_path", "d.json")
        assert controller.file_state.is_ready() is True

    def test_set_file_resets_mission(self, controller):
        controller.set_file("mission_path", "x.json")
        assert controller.mission is None

    def test_set_file_resets_eval_result(self, controller):
        controller.set_file("flight_path", "x.json")
        assert controller.eval_result is None


class TestLoadMissionConfig:
    def test_raises_when_path_empty(self, controller):
        with pytest.raises(FileLoadError):
            controller.load_mission_config()

    def test_raises_on_invalid_file(self, controller, tmp_path):
        bad = tmp_path / "bad.json"
        bad.write_text("not valid json", encoding="utf-8")
        controller.set_file("mission_path", str(bad))
        with pytest.raises(FileLoadError):
            controller.load_mission_config()

    def test_returns_mission_on_valid_file(self, tmp_path, controller):
        mission_path = tmp_path / "mission.json"
        _write_mission(mission_path)
        controller.set_file("mission_path", str(mission_path))
        mission = controller.load_mission_config()
        assert mission.mission_id == "test_mission"

    def test_stores_mission_on_controller(self, tmp_path, controller):
        mission_path = tmp_path / "mission.json"
        _write_mission(mission_path)
        controller.set_file("mission_path", str(mission_path))
        controller.load_mission_config()
        assert controller.mission is not None


class TestRunEvaluation:
    def test_raises_when_files_not_set(self, controller):
        with pytest.raises(EvaluationError):
            controller.run_evaluation()

    def test_returns_result_on_valid_input(self, ready_controller):
        result = ready_controller.run_evaluation()
        assert result is not None
        assert result.mission_id == "test_mission"

    def test_stores_result_on_controller(self, ready_controller):
        ready_controller.run_evaluation()
        assert ready_controller.eval_result is not None

    def test_progress_callback_called(self, ready_controller):
        calls: list[tuple[str, str, int]] = []
        ready_controller.run_evaluation(progress=lambda s, m, p: calls.append((s, m, p)))
        assert len(calls) > 0

    def test_stores_records_after_evaluation(self, ready_controller):
        ready_controller.run_evaluation()
        assert len(ready_controller.flight_records) > 0
        assert len(ready_controller.capture_records) > 0
        assert len(ready_controller.collision_records) > 0


class TestExportResults:
    def test_raises_when_no_eval_result(self, controller, tmp_path):
        from drone_eval.utils.exceptions import ExportError
        config = ExportConfig(output_dir=str(tmp_path))
        with pytest.raises(ExportError):
            controller.export_results(config)

    def test_saves_requested_files(self, ready_controller, tmp_path):
        ready_controller.run_evaluation()
        config = ExportConfig(
            output_dir=str(tmp_path / "out"),
            save_eval_result_json=True,
            save_eval_result_csv=False,
            save_eval_detail_csv=False,
            save_eval_summary_json=False,
        )
        Path(tmp_path / "out").mkdir()
        result = ready_controller.export_results(config, "2026-05-31")
        assert len(result.saved) == 1

    def test_save_result_tracks_failures(self, ready_controller, tmp_path):
        ready_controller.run_evaluation()
        config = ExportConfig(
            output_dir="/nonexistent/path/that/does/not/exist",
            save_eval_result_json=True,
        )
        result = ready_controller.export_results(config)
        assert len(result.failed) > 0
        assert not result.all_succeeded


class TestHistory:
    def test_load_history_empty_initially(self, controller):
        assert controller.load_history() == []

    def test_history_saved_after_export(self, ready_controller, tmp_path):
        ready_controller.run_evaluation()
        out = tmp_path / "out"
        out.mkdir()
        config = ExportConfig(output_dir=str(out))
        ready_controller.export_results(config, "2026-05-31 10:00:00")
        entries = ready_controller.load_history()
        assert len(entries) == 1

    def test_delete_history_entry(self, ready_controller, tmp_path):
        ready_controller.run_evaluation()
        out = tmp_path / "out"
        out.mkdir()
        config = ExportConfig(output_dir=str(out))
        ready_controller.export_results(config, "2026-05-31 10:00:00")
        entries = ready_controller.load_history()
        assert ready_controller.delete_history_entry(entries[0].entry_id) is True
        assert ready_controller.load_history() == []

    def test_clear_history(self, ready_controller, tmp_path):
        ready_controller.run_evaluation()
        out = tmp_path / "out"
        out.mkdir()
        config = ExportConfig(output_dir=str(out))
        ready_controller.export_results(config, "2026-05-31 10:00:00")
        ready_controller.clear_history()
        assert ready_controller.load_history() == []
