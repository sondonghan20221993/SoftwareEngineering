from dataclasses import dataclass
from typing import List


@dataclass
class Position:
    x: float
    y: float
    z: float


@dataclass
class Direction:
    yaw: float
    pitch: float


@dataclass
class TargetPoint:
    target_id: str
    position: Position
    direction: Direction
    time_limit: float


@dataclass
class Tolerance:
    position: float
    yaw: float
    pitch: float


@dataclass
class Weights:
    position: float
    direction: float


@dataclass
class DeductionPolicy:
    position: float
    yaw: float
    pitch: float
    timeout: float
    missing: float
    collision: float


@dataclass
class MissionConfig:
    mission_name: str
    targets: List[TargetPoint]
    tolerance: Tolerance
    weights: Weights
    deduction_policy: DeductionPolicy
