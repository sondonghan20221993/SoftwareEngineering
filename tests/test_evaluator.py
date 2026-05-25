from drone_eval.model.logs import CaptureRecord
from drone_eval.service.evaluator import Evaluator


def test_evaluator_counts_success_missing_collision_and_timeout(mission, flight_records, captures, collisions) -> None:
    result = Evaluator.evaluate(mission, flight_records, captures, collisions)
    assert result.total_targets == 2
    assert result.success_count == 1
    assert result.missing_count == 0
    assert result.collision_count == 1
    assert result.timeout_count == 1


def test_evaluator_uses_only_matched_targets_for_averages(mission, flight_records, tmp_path) -> None:
    capture_path = tmp_path / "cap.png"
    capture_path.write_bytes(b"img")
    result = Evaluator.evaluate(
        mission,
        flight_records,
        [CaptureRecord(20.0, 0.0, 0.0, -10.0, 0.0, -30.0, 90.0, str(capture_path))],
        [],
    )
    assert result.missing_count == 1
    assert result.avg_position_error == 0.0
    assert result.avg_yaw_error == 0.0
    assert result.avg_pitch_error == 0.0


def test_evaluator_sets_missing_target_timeout_deduction_to_zero(mission, flight_records) -> None:
    result = Evaluator.evaluate(mission, flight_records, [], [])
    assert [target.timeout_deduction for target in result.target_results] == [0.0, 0.0]
