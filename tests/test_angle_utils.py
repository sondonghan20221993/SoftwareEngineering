from drone_eval.utils.angle_utils import angle_diff_deg, normalize_angle


def test_normalize_angle_wraps_positive_values() -> None:
    assert normalize_angle(190.0) == -170.0


def test_normalize_angle_wraps_negative_values() -> None:
    assert normalize_angle(-190.0) == 170.0


def test_normalize_angle_keeps_180_as_negative_180() -> None:
    assert normalize_angle(180.0) == -180.0


def test_normalize_angle_zero_unchanged() -> None:
    assert normalize_angle(0.0) == 0.0


def test_normalize_angle_positive_quadrant_unchanged() -> None:
    assert normalize_angle(90.0) == 90.0


def test_normalize_angle_negative_quadrant_unchanged() -> None:
    assert normalize_angle(-90.0) == -90.0


def test_normalize_angle_360_wraps_to_zero() -> None:
    assert normalize_angle(360.0) == 0.0


def test_normalize_angle_negative_360_wraps_to_zero() -> None:
    assert normalize_angle(-360.0) == 0.0


def test_normalize_angle_just_under_180() -> None:
    assert normalize_angle(179.0) == 179.0


def test_normalize_angle_just_under_negative_180() -> None:
    assert normalize_angle(-179.0) == -179.0


def test_normalize_angle_540_wraps_correctly() -> None:
    assert normalize_angle(540.0) == -180.0


def test_angle_diff_deg_same_angle_is_zero() -> None:
    assert angle_diff_deg(45.0, 45.0) == 0.0


def test_angle_diff_deg_is_symmetric() -> None:
    assert angle_diff_deg(10.0, 30.0) == angle_diff_deg(30.0, 10.0)


def test_angle_diff_deg_wrap_around_zero() -> None:
    assert abs(angle_diff_deg(350.0, 10.0) - 20.0) < 1e-9


def test_angle_diff_deg_wrap_around_180() -> None:
    assert abs(angle_diff_deg(170.0, -170.0) - 20.0) < 1e-9


def test_angle_diff_deg_max_is_180() -> None:
    assert angle_diff_deg(0.0, 180.0) <= 180.0
    assert angle_diff_deg(0.0, -180.0) <= 180.0


def test_angle_diff_deg_result_is_non_negative() -> None:
    for a, b in [(-90.0, 90.0), (0.0, 270.0), (180.0, -180.0)]:
        assert angle_diff_deg(a, b) >= 0.0
