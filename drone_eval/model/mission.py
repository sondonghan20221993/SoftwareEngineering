from dataclasses import dataclass
from typing import List


@dataclass
class ScorePolicy:
    position_penalty_per_meter: float
    direction_yaw_penalty_per_degree: float
    direction_pitch_penalty_per_degree: float
    missing_capture_penalty: float
    collision_penalty: float
    timeout_penalty: float
    position_weight: float
    direction_weight: float


@dataclass
class TargetPoint:
    target_id: str
    x: float
    y: float
    z: float
    yaw: float
    pitch: float
    time_limit: float


@dataclass
class MissionConfig:
    mission_id: str
    allow_position_error: float
    allow_yaw_error: float
    allow_pitch_error: float
    targets: List[TargetPoint]
    score_policy: ScorePolicy
