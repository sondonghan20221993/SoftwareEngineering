from dataclasses import dataclass
from typing import Optional

from drone_eval.model.mission import Position, Direction


@dataclass
class CaptureRecord:
    timestamp: float
    position: Position
    direction: Direction
    image_path: str


@dataclass
class CollisionRecord:
    timestamp: float
    collision: bool
    position: Position
