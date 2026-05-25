from __future__ import annotations

import csv
import json
from dataclasses import asdict
from pathlib import Path

from drone_eval.model.result import EvalResult


class ReportExporter:
    @staticmethod
    def export_eval_result_json(result: EvalResult, path: str | Path) -> None:
        payload = {
            "mission_id": result.mission_id,
            "final_score": result.final_score,
            "total_targets": result.total_targets,
            "success_count": result.success_count,
            "missing_count": result.missing_count,
            "collision_count": result.collision_count,
            "timeout_count": result.timeout_count,
            "score_detail": asdict(result.score_detail),
        }
        Path(path).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    @staticmethod
    def export_eval_result_csv(result: EvalResult, path: str | Path) -> None:
        row = {
            "mission_id": result.mission_id,
            "final_score": result.final_score,
            "total_targets": result.total_targets,
            "success_count": result.success_count,
            "missing_count": result.missing_count,
            "collision_count": result.collision_count,
            "timeout_count": result.timeout_count,
            "total_position_deduction": result.score_detail.total_position_deduction,
            "total_direction_deduction": result.score_detail.total_direction_deduction,
            "total_missing_deduction": result.score_detail.total_missing_deduction,
            "total_collision_deduction": result.score_detail.total_collision_deduction,
            "total_timeout_deduction": result.score_detail.total_timeout_deduction,
            "total_deduction": result.score_detail.total_deduction,
            "base_score": result.score_detail.base_score,
        }
        ReportExporter._write_csv(Path(path), [row], list(row.keys()))

    @staticmethod
    def export_eval_detail_csv(result: EvalResult, path: str | Path) -> None:
        rows = []
        for target in result.target_results:
            rows.append(
                {
                    "target_id": target.target_id,
                    "matched_capture_timestamp": target.matched_capture_timestamp,
                    "position_error": target.position_error,
                    "yaw_error": target.yaw_error,
                    "pitch_error": target.pitch_error,
                    "position_ok": target.position_ok,
                    "direction_ok": target.direction_ok,
                    "time_ok": target.time_ok,
                    "image_linked": target.image_linked,
                    "is_missing": target.is_missing,
                    "is_timeout": target.is_timeout,
                    "position_deduction": target.position_deduction,
                    "direction_deduction": target.direction_deduction,
                    "timeout_deduction": target.timeout_deduction,
                }
            )
        fieldnames = [
            "target_id",
            "matched_capture_timestamp",
            "position_error",
            "yaw_error",
            "pitch_error",
            "position_ok",
            "direction_ok",
            "time_ok",
            "image_linked",
            "is_missing",
            "is_timeout",
            "position_deduction",
            "direction_deduction",
            "timeout_deduction",
        ]
        ReportExporter._write_csv(Path(path), rows, fieldnames)

    @staticmethod
    def export_eval_summary_json(result: EvalResult, path: str | Path) -> None:
        payload = {
            "mission_id": result.mission_id,
            "total_targets": result.total_targets,
            "success_count": result.success_count,
            "missing_count": result.missing_count,
            "collision_count": result.collision_count,
            "timeout_count": result.timeout_count,
            "avg_position_error": result.avg_position_error,
            "avg_yaw_error": result.avg_yaw_error,
            "avg_pitch_error": result.avg_pitch_error,
            "final_score": result.final_score,
        }
        Path(path).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    @staticmethod
    def _write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
        with path.open("w", encoding="utf-8", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
