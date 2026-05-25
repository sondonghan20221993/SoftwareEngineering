from __future__ import annotations

import csv
import json
from pathlib import Path

from drone_eval.model.logs import CaptureRecord, CollisionRecord, FlightRecord
from drone_eval.model.mission import MissionConfig, ScorePolicy, TargetPoint


class FileLoader:
    @staticmethod
    def load_mission_config(path: str | Path) -> MissionConfig:
        file_path = Path(path)
        data = json.loads(file_path.read_text(encoding="utf-8"))
        targets = [
            TargetPoint(
                target_id=item["target_id"],
                x=float(item["x"]),
                y=float(item["y"]),
                z=float(item["z"]),
                yaw=float(item["yaw"]),
                pitch=float(item["pitch"]),
                time_limit=float(item["time_limit"]),
            )
            for item in data["targets"]
        ]
        score_policy = ScorePolicy(
            position_penalty_per_meter=float(data["score_policy"]["position_penalty_per_meter"]),
            direction_yaw_penalty_per_degree=float(data["score_policy"]["direction_yaw_penalty_per_degree"]),
            direction_pitch_penalty_per_degree=float(data["score_policy"]["direction_pitch_penalty_per_degree"]),
            missing_capture_penalty=float(data["score_policy"]["missing_capture_penalty"]),
            collision_penalty=float(data["score_policy"]["collision_penalty"]),
            timeout_penalty=float(data["score_policy"]["timeout_penalty"]),
            position_weight=float(data["score_policy"]["position_weight"]),
            direction_weight=float(data["score_policy"]["direction_weight"]),
        )
        return MissionConfig(
            mission_id=data["mission_id"],
            allow_position_error=float(data["allow_position_error"]),
            allow_yaw_error=float(data["allow_yaw_error"]),
            allow_pitch_error=float(data["allow_pitch_error"]),
            targets=targets,
            score_policy=score_policy,
        )

    @staticmethod
    def load_flight_records(path: str | Path) -> list[FlightRecord]:
        return FileLoader._load_records(Path(path), FileLoader._flight_from_dict)

    @staticmethod
    def load_capture_records(path: str | Path) -> list[CaptureRecord]:
        return FileLoader._load_records(Path(path), FileLoader._capture_from_dict)

    @staticmethod
    def load_collision_records(path: str | Path) -> list[CollisionRecord]:
        return FileLoader._load_records(Path(path), FileLoader._collision_from_dict)

    @staticmethod
    def _load_records(path: Path, parser):
        if path.suffix.lower() == ".csv":
            with path.open("r", encoding="utf-8", newline="") as file:
                return [parser(row) for row in csv.DictReader(file)]
        if path.suffix.lower() == ".json":
            data = json.loads(path.read_text(encoding="utf-8"))
            return [parser(row) for row in data]
        raise ValueError(f"Unsupported file extension: {path.suffix}")

    @staticmethod
    def _flight_from_dict(row: dict[str, str]) -> FlightRecord:
        return FlightRecord(
            timestamp=float(row["timestamp"]),
            x=float(row["x"]),
            y=float(row["y"]),
            z=float(row["z"]),
            roll=float(row["roll"]),
            pitch=float(row["pitch"]),
            yaw=float(row["yaw"]),
            speed=float(row["speed"]),
        )

    @staticmethod
    def _capture_from_dict(row: dict[str, str]) -> CaptureRecord:
        return CaptureRecord(
            timestamp=float(row["timestamp"]),
            x=float(row["x"]),
            y=float(row["y"]),
            z=float(row["z"]),
            roll=float(row["roll"]),
            pitch=float(row["pitch"]),
            yaw=float(row["yaw"]),
            image_path=str(row["image_path"]),
        )

    @staticmethod
    def _collision_from_dict(row: dict[str, str]) -> CollisionRecord:
        return CollisionRecord(
            timestamp=float(row["timestamp"]),
            collision=FileLoader._parse_bool(row["collision"]),
            x=float(row["x"]),
            y=float(row["y"]),
            z=float(row["z"]),
        )

    @staticmethod
    def _parse_bool(value: object) -> bool:
        if isinstance(value, bool):
            return value
        normalized = str(value).strip().lower()
        return normalized in {"true", "1", "yes", "y"}
