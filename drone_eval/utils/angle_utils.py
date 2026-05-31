def normalize_angle_deg(angle: float) -> float:
    """Normalize angle in degrees to the range [-180, 180).

    Examples:
        180 -> -180
        181 -> -179
    """
    return ((angle + 180.0) % 360.0) - 180.0


normalize_angle = normalize_angle_deg


def angle_diff_deg(a: float, b: float) -> float:
    """Return the minimal absolute difference between two angles (degrees).

    The result is in [0, 180].
    """
    diff = normalize_angle_deg(a - b)
    return abs(diff)
