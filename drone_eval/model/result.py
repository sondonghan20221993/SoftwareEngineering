from dataclasses import dataclass, field
from typing import Optional

from drone_eval.model.logs import CaptureRecord, CollisionRecord


@dataclass
class TargetResult:
    target_id: str = ""
    matched_capture: Optional[CaptureRecord] = None
    matched_capture_timestamp: Optional[float] = None
    position_error: Optional[float] = None
    yaw_error: Optional[float] = None
    pitch_error: Optional[float] = None
    position_ok: bool = False
    direction_ok: bool = False
    time_ok: bool = False
    image_linked: bool = False
    is_missing: bool = False
    is_timeout: bool = False
    position_deduction: float = 0.0
    direction_deduction: float = 0.0
    timeout_deduction: float = 0.0


@dataclass
class ScoreDetail:
    total_position_deduction: float = 0.0
    total_direction_deduction: float = 0.0
    total_missing_deduction: float = 0.0
    total_collision_deduction: float = 0.0
    total_timeout_deduction: float = 0.0
    total_deduction: float = 0.0
    base_score: float = 100.0


@dataclass
class EvalResult:
    mission_id: str = ""
    target_results: list[TargetResult] = field(default_factory=list)
    collision_records: list[CollisionRecord] = field(default_factory=list)
    total_targets: int = 0
    success_count: int = 0
    missing_count: int = 0
    collision_count: int = 0
    timeout_count: int = 0
    avg_position_error: Optional[float] = None
    avg_yaw_error: Optional[float] = None
    avg_pitch_error: Optional[float] = None
    score_detail: ScoreDetail = field(default_factory=ScoreDetail)
    final_score: float = 0.0
