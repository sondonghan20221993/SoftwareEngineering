from dataclasses import dataclass


@dataclass
class FlightRecord:
    timestamp: float
    x: float
    y: float
    z: float
    roll: float
    pitch: float
    yaw: float
    speed: float


@dataclass
class CaptureRecord:
    timestamp: float
    x: float
    y: float
    z: float
    roll: float
    pitch: float
    yaw: float
    image_path: str


@dataclass
class CollisionRecord:
    timestamp: float
    collision: bool
    x: float
    y: float
    z: float
