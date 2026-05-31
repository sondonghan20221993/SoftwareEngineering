from pathlib import Path

import pytest

from drone_eval.model.logs import CaptureRecord, CollisionRecord, FlightRecord
from drone_eval.model.mission import MissionConfig, ScorePolicy, TargetPoint


@pytest.fixture
def mission() -> MissionConfig:
    return MissionConfig(
        mission_id="mission_001",
        allow_position_error=2.0,
        allow_yaw_error=10.0,
        allow_pitch_error=10.0,
        targets=[
            TargetPoint("T1", 0.0, 0.0, -10.0, 90.0, -30.0, 60.0),
            TargetPoint("T2", 20.0, 0.0, -10.0, 0.0, -20.0, 30.0),
        ],
        score_policy=ScorePolicy(
            position_penalty_per_meter=5.0,
            direction_yaw_penalty_per_degree=2.0,
            direction_pitch_penalty_per_degree=2.0,
            missing_capture_penalty=10.0,
            collision_penalty=20.0,
            timeout_penalty=5.0,
            position_weight=1.0,
            direction_weight=1.0,
        ),
    )


@pytest.fixture
def flight_records() -> list[FlightRecord]:
    return [FlightRecord(10.0, 0.0, 0.0, -10.0, 0.0, -30.0, 90.0, 3.0)]


@pytest.fixture
def captures(tmp_path: Path) -> list[CaptureRecord]:
    existing = tmp_path / "cap1.png"
    existing.write_bytes(b"img")
    return [
        CaptureRecord(20.0, 0.5, 0.5, -10.0, 0.0, -28.0, 92.0, str(existing)),
        CaptureRecord(50.0, 20.0, 0.0, -10.0, 0.0, -10.0, 30.0, str(tmp_path / "missing.png")),
    ]


@pytest.fixture
def collisions() -> list[CollisionRecord]:
    return [
        CollisionRecord(12.0, False, 0.0, 0.0, -10.0),
        CollisionRecord(14.0, True, 1.0, 1.0, -9.0),
    ]
