from drone_eval.model.logs import CaptureRecord
from drone_eval.service.matcher import Matcher, calculate_cost


def test_cost_is_lower_for_better_capture(mission, tmp_path) -> None:
    near = CaptureRecord(10.0, 0.0, 0.0, -10.0, 0.0, -30.0, 90.0, str(tmp_path / "a.png"))
    far = CaptureRecord(10.0, 10.0, 10.0, -30.0, 0.0, 10.0, -90.0, str(tmp_path / "b.png"))
    assert calculate_cost(mission.targets[0], near, mission) < calculate_cost(mission.targets[0], far, mission)


def test_matcher_finds_one_to_one_minimum_cost_mapping(mission, tmp_path) -> None:
    captures = [
        CaptureRecord(10.0, 20.0, 0.0, -10.0, 0.0, -20.0, 0.0, str(tmp_path / "a.png")),
        CaptureRecord(10.0, 0.0, 0.0, -10.0, 0.0, -30.0, 90.0, str(tmp_path / "b.png")),
    ]
    mapping = Matcher.match(mission.targets, captures, mission)
    assert mapping == {0: 1, 1: 0}


def test_matcher_leaves_unmatched_targets_when_captures_are_fewer(mission, tmp_path) -> None:
    captures = [CaptureRecord(10.0, 0.0, 0.0, -10.0, 0.0, -30.0, 90.0, str(tmp_path / "a.png"))]
    mapping = Matcher.match(mission.targets, captures, mission)
    assert mapping == {0: 0}


def test_matcher_ignores_extra_captures_when_targets_are_fewer(mission, tmp_path) -> None:
    captures = [
        CaptureRecord(10.0, 0.0, 0.0, -10.0, 0.0, -30.0, 90.0, str(tmp_path / "a.png")),
        CaptureRecord(10.0, 20.0, 0.0, -10.0, 0.0, -20.0, 0.0, str(tmp_path / "b.png")),
        CaptureRecord(10.0, 999.0, 999.0, -999.0, 0.0, 80.0, -80.0, str(tmp_path / "c.png")),
    ]
    mapping = Matcher.match(mission.targets, captures, mission)
    assert mapping == {0: 0, 1: 1}
