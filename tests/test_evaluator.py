import math

from drone_eval.model.logs import CaptureRecord, CollisionRecord
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


def test_evaluator_all_missing_when_no_captures(mission, flight_records) -> None:
    result = Evaluator.evaluate(mission, flight_records, [], [])
    assert result.missing_count == len(mission.targets)
    assert result.success_count == 0


def test_evaluator_avg_errors_none_when_all_missing(mission, flight_records) -> None:
    result = Evaluator.evaluate(mission, flight_records, [], [])
    assert result.avg_position_error is None
    assert result.avg_yaw_error is None
    assert result.avg_pitch_error is None


def test_evaluator_final_score_not_below_zero(mission, flight_records) -> None:
    result = Evaluator.evaluate(mission, flight_records, [], [
        CollisionRecord(1.0, True, 0.0, 0.0, -10.0),
        CollisionRecord(2.0, True, 1.0, 0.0, -10.0),
        CollisionRecord(3.0, True, 2.0, 0.0, -10.0),
    ])
    assert result.final_score >= 0.0


def test_evaluator_mission_start_time_is_first_flight_timestamp(mission, flight_records, captures) -> None:
    result = Evaluator.evaluate(mission, flight_records, captures, [])
    assert result.mission_start_time == flight_records[0].timestamp


def test_evaluator_all_succeed_when_captures_are_perfect(mission, flight_records, tmp_path) -> None:
    img1 = tmp_path / "c1.png"
    img2 = tmp_path / "c2.png"
    img1.write_bytes(b"img")
    img2.write_bytes(b"img")
    t1, t2 = mission.targets
    perfect_captures = [
        CaptureRecord(20.0, t1.x, t1.y, t1.z, 0.0, t1.pitch, t1.yaw, str(img1)),
        CaptureRecord(25.0, t2.x, t2.y, t2.z, 0.0, t2.pitch, t2.yaw, str(img2)),
    ]
    result = Evaluator.evaluate(mission, flight_records, perfect_captures, [])
    assert result.success_count == 2
    assert result.missing_count == 0


def test_evaluator_position_error_calculated_correctly(mission, flight_records, tmp_path) -> None:
    img = tmp_path / "cap.png"
    img.write_bytes(b"img")
    t = mission.targets[0]
    dx, dy, dz = 3.0, 4.0, 0.0
    capture = CaptureRecord(20.0, t.x + dx, t.y + dy, t.z + dz, 0.0, t.pitch, t.yaw, str(img))
    result = Evaluator.evaluate(mission, flight_records, [capture], [])
    matched = result.target_results[0]
    assert matched.position_error is not None
    assert abs(matched.position_error - 5.0) < 1e-9


def test_evaluator_time_ok_false_when_capture_exceeds_limit(mission, flight_records, tmp_path) -> None:
    img = tmp_path / "cap.png"
    img.write_bytes(b"img")
    t = mission.targets[0]
    late_ts = flight_records[0].timestamp + t.time_limit + 1.0
    capture = CaptureRecord(late_ts, t.x, t.y, t.z, 0.0, t.pitch, t.yaw, str(img))
    result = Evaluator.evaluate(mission, flight_records, [capture], [])
    assert result.target_results[0].time_ok is False
    assert result.target_results[0].is_timeout is True


def test_evaluator_position_ok_true_within_tolerance(mission, flight_records, tmp_path) -> None:
    img = tmp_path / "cap.png"
    img.write_bytes(b"img")
    t = mission.targets[0]
    capture = CaptureRecord(20.0, t.x + mission.allow_position_error - 0.1,
                            t.y, t.z, 0.0, t.pitch, t.yaw, str(img))
    result = Evaluator.evaluate(mission, flight_records, [capture], [])
    assert result.target_results[0].position_ok is True


def test_evaluator_counts_only_true_collision_records(mission, flight_records) -> None:
    collisions = [
        CollisionRecord(1.0, False, 0.0, 0.0, -10.0),
        CollisionRecord(2.0, True, 1.0, 0.0, -10.0),
        CollisionRecord(3.0, False, 2.0, 0.0, -10.0),
        CollisionRecord(4.0, True, 3.0, 0.0, -10.0),
    ]
    result = Evaluator.evaluate(mission, flight_records, [], collisions)
    assert result.collision_count == 2


def test_evaluator_image_linked_false_for_missing_file(mission, flight_records, tmp_path) -> None:
    t = mission.targets[0]
    capture = CaptureRecord(20.0, t.x, t.y, t.z, 0.0, t.pitch, t.yaw,
                            str(tmp_path / "nonexistent.png"))
    result = Evaluator.evaluate(mission, flight_records, [capture], [])
    assert result.target_results[0].image_linked is False


def test_evaluator_total_targets_equals_mission_targets(mission, flight_records) -> None:
    result = Evaluator.evaluate(mission, flight_records, [], [])
    assert result.total_targets == len(mission.targets)
