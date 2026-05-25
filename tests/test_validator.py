from drone_eval.model.logs import CaptureRecord, CollisionRecord, FlightRecord
from drone_eval.service.validator import Validator


def test_validate_mission_rejects_duplicate_target_ids(mission) -> None:
    mission.targets.append(mission.targets[0])

    errors = Validator.validate_mission_config(mission)

    assert any("duplicate" in error.lower() for error in errors)


def test_validate_mission_rejects_zero_weight(mission) -> None:
    mission.score_policy.position_weight = 0.0

    errors = Validator.validate_mission_config(mission)

    assert any("position_weight" in error for error in errors)


def test_validate_flight_records_rejects_nan_values() -> None:
    records = [FlightRecord(1.0, float("nan"), 0.0, -10.0, 0.0, -30.0, 90.0, 3.0)]

    errors = Validator.validate_flight_records(records)

    assert any("nan" in error.lower() for error in errors)


def test_validate_capture_records_checks_orientation_nan(tmp_path) -> None:
    image_path = tmp_path / "cap.png"
    image_path.write_bytes(b"img")
    records = [CaptureRecord(1.0, 0.0, 0.0, -10.0, 0.0, float("nan"), 90.0, str(image_path))]

    errors = Validator.validate_capture_records(records)

    assert any("pitch" in error.lower() for error in errors)


def test_validate_capture_records_flags_missing_image(tmp_path) -> None:
    records = [CaptureRecord(1.0, 0.0, 0.0, -10.0, 0.0, -30.0, 90.0, str(tmp_path / "missing.png"))]

    errors = Validator.validate_capture_records(records)

    assert any("image" in error.lower() for error in errors)


def test_validate_collision_records_checks_nan_values() -> None:
    records = [CollisionRecord(1.0, True, float("nan"), 0.0, -10.0)]

    errors = Validator.validate_collision_records(records)

    assert any("nan" in error.lower() for error in errors)
