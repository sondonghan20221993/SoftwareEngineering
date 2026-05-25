from drone_eval.utils.angle_utils import normalize_angle


def test_normalize_angle_wraps_positive_values() -> None:
    assert normalize_angle(190.0) == -170.0


def test_normalize_angle_wraps_negative_values() -> None:
    assert normalize_angle(-190.0) == 170.0


def test_normalize_angle_keeps_180_as_negative_180() -> None:
    assert normalize_angle(180.0) == -180.0
