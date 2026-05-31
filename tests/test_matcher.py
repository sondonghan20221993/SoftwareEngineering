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


def test_matcher_returns_empty_when_targets_empty(mission, tmp_path) -> None:
    capture = CaptureRecord(10.0, 0.0, 0.0, -10.0, 0.0, -30.0, 90.0, str(tmp_path / "a.png"))
    mapping = Matcher.match([], [capture], mission)
    assert mapping == {}


def test_matcher_returns_empty_when_captures_empty(mission) -> None:
    mapping = Matcher.match(mission.targets, [], mission)
    assert mapping == {}


def test_matcher_returns_empty_when_both_empty(mission) -> None:
    mapping = Matcher.match([], [], mission)
    assert mapping == {}


def test_cost_is_zero_for_perfect_match(mission, tmp_path) -> None:
    t = mission.targets[0]
    perfect = CaptureRecord(10.0, t.x, t.y, t.z, 0.0, t.pitch, t.yaw, str(tmp_path / "a.png"))
    cost = calculate_cost(t, perfect, mission)
    assert cost == 0.0


def test_cost_increases_with_position_error(mission, tmp_path) -> None:
    t = mission.targets[0]
    near = CaptureRecord(10.0, t.x + 1.0, t.y, t.z, 0.0, t.pitch, t.yaw, str(tmp_path / "a.png"))
    far = CaptureRecord(10.0, t.x + 5.0, t.y, t.z, 0.0, t.pitch, t.yaw, str(tmp_path / "b.png"))
    assert calculate_cost(t, near, mission) < calculate_cost(t, far, mission)


def test_cost_increases_with_direction_error(mission, tmp_path) -> None:
    t = mission.targets[0]
    small_diff = CaptureRecord(10.0, t.x, t.y, t.z, 0.0, t.pitch, t.yaw + 5.0, str(tmp_path / "a.png"))
    large_diff = CaptureRecord(10.0, t.x, t.y, t.z, 0.0, t.pitch, t.yaw + 30.0, str(tmp_path / "b.png"))
    assert calculate_cost(t, small_diff, mission) < calculate_cost(t, large_diff, mission)


def test_each_capture_assigned_to_at_most_one_target(mission, tmp_path) -> None:
    captures = [
        CaptureRecord(10.0, 0.0, 0.0, -10.0, 0.0, -30.0, 90.0, str(tmp_path / "a.png")),
        CaptureRecord(10.0, 20.0, 0.0, -10.0, 0.0, -20.0, 0.0, str(tmp_path / "b.png")),
    ]
    mapping = Matcher.match(mission.targets, captures, mission)
    assigned_captures = list(mapping.values())
    assert len(assigned_captures) == len(set(assigned_captures))


def test_each_target_assigned_at_most_once(mission, tmp_path) -> None:
    captures = [
        CaptureRecord(10.0, 0.0, 0.0, -10.0, 0.0, -30.0, 90.0, str(tmp_path / "a.png")),
        CaptureRecord(10.0, 20.0, 0.0, -10.0, 0.0, -20.0, 0.0, str(tmp_path / "b.png")),
    ]
    mapping = Matcher.match(mission.targets, captures, mission)
    assigned_targets = list(mapping.keys())
    assert len(assigned_targets) == len(set(assigned_targets))
