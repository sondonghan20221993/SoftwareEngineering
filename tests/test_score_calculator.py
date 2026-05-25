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
