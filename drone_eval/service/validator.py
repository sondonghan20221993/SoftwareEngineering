import math
from pathlib import Path

from drone_eval.model.logs import CaptureRecord, CollisionRecord, FlightRecord
from drone_eval.model.mission import MissionConfig


class Validator:
    @staticmethod
    def validate_mission_config(mission: MissionConfig) -> list[str]:
        errors: list[str] = []
        if not mission.targets:
            errors.append("targets must not be empty")

        target_ids = [target.target_id for target in mission.targets]
        if len(target_ids) != len(set(target_ids)):
            errors.append("duplicate target_id detected")

        if mission.allow_position_error < 0:
            errors.append("allow_position_error must be >= 0")
        if mission.allow_yaw_error < 0:
            errors.append("allow_yaw_error must be >= 0")
        if mission.allow_pitch_error < 0:
            errors.append("allow_pitch_error must be >= 0")
        if mission.score_policy.position_weight <= 0:
            errors.append("position_weight must be > 0")
        if mission.score_policy.direction_weight <= 0:
            errors.append("direction_weight must be > 0")

        numeric_policy_fields = {
            "position_penalty_per_meter": mission.score_policy.position_penalty_per_meter,
            "direction_yaw_penalty_per_degree": mission.score_policy.direction_yaw_penalty_per_degree,
            "direction_pitch_penalty_per_degree": mission.score_policy.direction_pitch_penalty_per_degree,
            "missing_capture_penalty": mission.score_policy.missing_capture_penalty,
            "collision_penalty": mission.score_policy.collision_penalty,
            "timeout_penalty": mission.score_policy.timeout_penalty,
        }
        for field_name, value in numeric_policy_fields.items():
            if value < 0:
                errors.append(f"{field_name} must be >= 0")
        return errors

    @staticmethod
    def validate_flight_records(records: list[FlightRecord]) -> list[str]:
        errors: list[str] = []
        for index, record in enumerate(records):
            Validator._check_numeric_fields(
                errors,
                index,
                {
                    "timestamp": record.timestamp,
                    "x": record.x,
                    "y": record.y,
                    "z": record.z,
                    "roll": record.roll,
                    "pitch": record.pitch,
                    "yaw": record.yaw,
                    "speed": record.speed,
                },
                "flight",
            )
        return errors

    @staticmethod
    def validate_capture_records(records: list[CaptureRecord]) -> list[str]:
        errors: list[str] = []
        for index, record in enumerate(records):
            Validator._check_numeric_fields(
                errors,
                index,
                {
                    "timestamp": record.timestamp,
                    "x": record.x,
                    "y": record.y,
                    "z": record.z,
                    "roll": record.roll,
                    "pitch": record.pitch,
                    "yaw": record.yaw,
                },
                "capture",
            )
            if not record.image_path:
                errors.append(f"capture record {index}: image_path is required")
            elif not Path(record.image_path).is_file():
                errors.append(f"capture record {index}: image file not found")
        return errors

    @staticmethod
    def validate_collision_records(records: list[CollisionRecord]) -> list[str]:
        errors: list[str] = []
        for index, record in enumerate(records):
            Validator._check_numeric_fields(
                errors,
                index,
                {
                    "timestamp": record.timestamp,
                    "x": record.x,
                    "y": record.y,
                    "z": record.z,
                },
                "collision",
            )
        return errors

    @staticmethod
    def _check_numeric_fields(
        errors: list[str],
        index: int,
        fields: dict[str, float],
        record_type: str,
    ) -> None:
        for field_name, value in fields.items():
            if math.isnan(value):
                errors.append(f"{record_type} record {index}: {field_name} is NaN")
