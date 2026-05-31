from drone_eval.model.result import TargetResult
from drone_eval.service.score_calculator import ScoreCalculator


def test_position_deduction_uses_excess_only(mission) -> None:
    assert ScoreCalculator.calculate_position_deduction(3.5, mission) == 7.5


def test_direction_deduction_sums_yaw_and_pitch_excess(mission) -> None:
    assert ScoreCalculator.calculate_direction_deduction(15.0, 14.0, mission) == 18.0


def test_missing_target_has_zero_timeout_deduction(mission) -> None:
    assert ScoreCalculator.calculate_timeout_deduction(True, False, mission) == 0.0


def test_final_score_has_zero_floor(mission) -> None:
    results = [
        TargetResult("T1", None, None, None, None, None, False, False, False, False, True, False, 90.0, 30.0, 0.0),
        TargetResult("T2", None, None, None, None, None, False, False, False, False, True, False, 20.0, 10.0, 0.0),
    ]
    _, final_score = ScoreCalculator.summarize(results, 3, mission)
    assert final_score == 0.0


def test_position_deduction_zero_within_tolerance(mission) -> None:
    assert ScoreCalculator.calculate_position_deduction(1.0, mission) == 0.0


def test_position_deduction_zero_at_exact_tolerance(mission) -> None:
    assert ScoreCalculator.calculate_position_deduction(mission.allow_position_error, mission) == 0.0


def test_position_deduction_grows_linearly_with_excess(mission) -> None:
    d1 = ScoreCalculator.calculate_position_deduction(4.0, mission)
    d2 = ScoreCalculator.calculate_position_deduction(6.0, mission)
    assert abs(d2 - d1 - 2.0 * mission.score_policy.position_penalty_per_meter) < 1e-9


def test_direction_deduction_zero_within_both_tolerances(mission) -> None:
    assert ScoreCalculator.calculate_direction_deduction(5.0, 5.0, mission) == 0.0


def test_direction_deduction_zero_at_exact_tolerances(mission) -> None:
    assert ScoreCalculator.calculate_direction_deduction(
        mission.allow_yaw_error, mission.allow_pitch_error, mission
    ) == 0.0


def test_direction_deduction_yaw_only_when_pitch_within_tolerance(mission) -> None:
    yaw_excess = 5.0
    deduction = ScoreCalculator.calculate_direction_deduction(
        mission.allow_yaw_error + yaw_excess, 0.0, mission
    )
    expected = yaw_excess * mission.score_policy.direction_yaw_penalty_per_degree
    assert abs(deduction - expected) < 1e-9


def test_direction_deduction_pitch_only_when_yaw_within_tolerance(mission) -> None:
    pitch_excess = 4.0
    deduction = ScoreCalculator.calculate_direction_deduction(
        0.0, mission.allow_pitch_error + pitch_excess, mission
    )
    expected = pitch_excess * mission.score_policy.direction_pitch_penalty_per_degree
    assert abs(deduction - expected) < 1e-9


def test_timeout_deduction_zero_when_time_ok(mission) -> None:
    assert ScoreCalculator.calculate_timeout_deduction(False, True, mission) == 0.0


def test_timeout_deduction_penalty_when_not_time_ok(mission) -> None:
    deduction = ScoreCalculator.calculate_timeout_deduction(False, False, mission)
    assert deduction == mission.score_policy.timeout_penalty


def test_summarize_score_100_when_no_deductions(mission) -> None:
    results = [
        TargetResult("T1", position_deduction=0.0, direction_deduction=0.0, timeout_deduction=0.0),
        TargetResult("T2", position_deduction=0.0, direction_deduction=0.0, timeout_deduction=0.0),
    ]
    _, score = ScoreCalculator.summarize(results, 0, mission)
    assert score == 100.0


def test_summarize_missing_penalty_multiplied_by_count(mission) -> None:
    results = [
        TargetResult("T1", is_missing=True, position_deduction=0.0, direction_deduction=0.0, timeout_deduction=0.0),
        TargetResult("T2", is_missing=True, position_deduction=0.0, direction_deduction=0.0, timeout_deduction=0.0),
    ]
    detail, _ = ScoreCalculator.summarize(results, 0, mission)
    assert detail.total_missing_deduction == 2 * mission.score_policy.missing_capture_penalty


def test_summarize_collision_penalty_multiplied_by_count(mission) -> None:
    results = [
        TargetResult("T1", position_deduction=0.0, direction_deduction=0.0, timeout_deduction=0.0),
    ]
    detail, _ = ScoreCalculator.summarize(results, 2, mission)
    assert detail.total_collision_deduction == 2 * mission.score_policy.collision_penalty


def test_summarize_total_deduction_is_sum_of_all_parts(mission) -> None:
    results = [
        TargetResult("T1", is_missing=False, position_deduction=5.0,
                     direction_deduction=4.0, timeout_deduction=3.0),
    ]
    detail, _ = ScoreCalculator.summarize(results, 1, mission)
    expected_total = 5.0 + 4.0 + 3.0 + mission.score_policy.missing_capture_penalty * 0 + mission.score_policy.collision_penalty
    assert abs(detail.total_deduction - expected_total) < 1e-9
