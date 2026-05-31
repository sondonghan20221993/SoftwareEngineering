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


def _make_full_result(mission_id: str = "m1", score: float = 100.0) -> EvalResult:
    return EvalResult(
        mission_id=mission_id,
        final_score=score,
        total_targets=2,
        success_count=2,
        missing_count=0,
        collision_count=0,
        timeout_count=0,
        score_detail=ScoreDetail(
            total_position_deduction=0.0,
            total_direction_deduction=0.0,
            total_missing_deduction=0.0,
            total_collision_deduction=0.0,
            total_timeout_deduction=0.0,
            total_deduction=0.0,
            base_score=100.0,
        ),
    )


def test_export_eval_result_json_creates_file(tmp_path) -> None:
    result = _make_full_result()
    path = tmp_path / "out.json"
    ReportExporter.export_eval_result_json(result, path)
    assert path.exists()
    assert path.stat().st_size > 0


def test_export_eval_result_json_mission_id_preserved(tmp_path) -> None:
    result = _make_full_result(mission_id="abc_mission")
    path = tmp_path / "out.json"
    ReportExporter.export_eval_result_json(result, path)
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["mission_id"] == "abc_mission"


def test_export_eval_detail_csv_has_required_columns(tmp_path) -> None:
    result = EvalResult(mission_id="m1", target_results=[
        TargetResult("T1", position_deduction=0.0, direction_deduction=0.0, timeout_deduction=0.0),
    ])
    path = tmp_path / "detail.csv"
    ReportExporter.export_eval_detail_csv(result, path)
    with path.open(encoding="utf-8") as f:
        headers = csv.DictReader(f).fieldnames or []
    for col in ["target_id", "position_error", "yaw_error", "pitch_error",
                "position_ok", "direction_ok", "time_ok", "is_missing"]:
        assert col in headers


def test_export_eval_detail_csv_empty_targets(tmp_path) -> None:
    result = EvalResult(mission_id="m1", target_results=[])
    path = tmp_path / "detail.csv"
    ReportExporter.export_eval_detail_csv(result, path)
    with path.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert rows == []


def test_export_eval_result_csv_contains_counts(tmp_path) -> None:
    result = EvalResult(
        mission_id="m1", total_targets=4, success_count=3,
        missing_count=1, collision_count=0, timeout_count=1,
        final_score=85.0,
        score_detail=ScoreDetail(
            total_position_deduction=0.0, total_direction_deduction=0.0,
            total_missing_deduction=10.0, total_collision_deduction=0.0,
            total_timeout_deduction=0.0, total_deduction=10.0, base_score=100.0,
        ),
    )
    path = tmp_path / "result.csv"
    ReportExporter.export_eval_result_csv(result, path)
    with path.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert rows[0]["total_targets"] == "4"
    assert rows[0]["success_count"] == "3"
    assert rows[0]["missing_count"] == "1"


def test_export_eval_detail_csv_deductions_preserved(tmp_path) -> None:
    result = EvalResult(mission_id="m1", target_results=[
        TargetResult("T1", position_deduction=3.5, direction_deduction=2.0, timeout_deduction=5.0),
    ])
    path = tmp_path / "detail.csv"
    ReportExporter.export_eval_detail_csv(result, path)
    with path.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert rows[0]["position_deduction"] == "3.5"
    assert rows[0]["direction_deduction"] == "2.0"
    assert rows[0]["timeout_deduction"] == "5.0"


def test_export_eval_summary_json_avg_errors_none_preserved(tmp_path) -> None:
    result = EvalResult(mission_id="m1", avg_position_error=None, final_score=50.0)
    path = tmp_path / "summary.json"
    ReportExporter.export_eval_summary_json(result, path)
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["avg_position_error"] is None


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
