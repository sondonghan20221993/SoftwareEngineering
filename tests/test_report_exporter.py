import csv
import json

from drone_eval.model.result import EvalResult, ScoreDetail, TargetResult
from drone_eval.service.report_exporter import ReportExporter


def test_export_eval_result_json_writes_expected_summary(tmp_path) -> None:
    result = EvalResult(
        mission_id="mission_001",
        total_targets=2,
        success_count=1,
        missing_count=1,
        collision_count=2,
        timeout_count=1,
        score_detail=ScoreDetail(
            total_position_deduction=8.0,
            total_direction_deduction=4.5,
            total_missing_deduction=10.0,
            total_collision_deduction=40.0,
            total_timeout_deduction=5.0,
            total_deduction=67.5,
            base_score=100.0,
        ),
        final_score=32.5,
    )

    output_path = tmp_path / "eval_result.json"
    ReportExporter.export_eval_result_json(result, output_path)

    data = json.loads(output_path.read_text(encoding="utf-8"))
    assert data["mission_id"] == "mission_001"
    assert data["score_detail"]["total_timeout_deduction"] == 5.0
    assert data["final_score"] == 32.5


def test_export_eval_result_csv_flattens_summary_into_single_row(tmp_path) -> None:
    result = EvalResult(
        mission_id="mission_001",
        total_targets=2,
        success_count=1,
        missing_count=1,
        collision_count=2,
        timeout_count=1,
        score_detail=ScoreDetail(
            total_position_deduction=8.0,
            total_direction_deduction=4.5,
            total_missing_deduction=10.0,
            total_collision_deduction=40.0,
            total_timeout_deduction=5.0,
            total_deduction=67.5,
            base_score=100.0,
        ),
        final_score=32.5,
    )

    output_path = tmp_path / "eval_result.csv"
    ReportExporter.export_eval_result_csv(result, output_path)

    with output_path.open("r", encoding="utf-8", newline="") as file:
        rows = list(csv.DictReader(file))

    assert len(rows) == 1
    assert rows[0]["mission_id"] == "mission_001"
    assert rows[0]["total_timeout_deduction"] == "5.0"
    assert rows[0]["final_score"] == "32.5"


def test_export_eval_detail_csv_includes_matched_capture_timestamp(tmp_path) -> None:
    result = EvalResult(
        mission_id="mission_001",
        target_results=[
            TargetResult(
                target_id="T1",
                matched_capture_timestamp=20.0,
                position_error=1.2,
                yaw_error=5.0,
                pitch_error=3.0,
                position_ok=True,
                direction_ok=True,
                time_ok=True,
                image_linked=True,
                is_missing=False,
                is_timeout=False,
                position_deduction=0.0,
                direction_deduction=0.0,
                timeout_deduction=0.0,
            ),
            TargetResult(
                target_id="T2",
                is_missing=True,
                image_linked=False,
            ),
        ],
    )

    output_path = tmp_path / "eval_detail.csv"
    ReportExporter.export_eval_detail_csv(result, output_path)

    with output_path.open("r", encoding="utf-8", newline="") as file:
        rows = list(csv.DictReader(file))

    assert rows[0]["matched_capture_timestamp"] == "20.0"
    assert rows[1]["matched_capture_timestamp"] == ""
    assert rows[1]["is_missing"] == "True"


def test_export_eval_summary_json_writes_core_aggregates(tmp_path) -> None:
    result = EvalResult(
        mission_id="mission_001",
        total_targets=5,
        success_count=3,
        missing_count=1,
        collision_count=2,
        timeout_count=1,
        avg_position_error=1.8,
        avg_yaw_error=6.2,
        avg_pitch_error=4.1,
        final_score=72.5,
    )

    output_path = tmp_path / "eval_summary.json"
    ReportExporter.export_eval_summary_json(result, output_path)

    data = json.loads(output_path.read_text(encoding="utf-8"))
    assert data["collision_count"] == 2
    assert data["avg_position_error"] == 1.8
    assert data["final_score"] == 72.5
