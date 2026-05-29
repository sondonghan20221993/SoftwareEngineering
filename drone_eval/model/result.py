from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class TargetResult:
    target_id: str
    matched_capture_timestamp: Optional[float]
    position_error: Optional[float]
    yaw_error: Optional[float]
    pitch_error: Optional[float]
    position_ok: bool
    direction_ok: bool
    time_ok: bool
    missing: bool
    success: bool
    deduction: float


@dataclass
class ScoreDetail:
    position_deduction: float
    yaw_deduction: float
    pitch_deduction: float
    timeout_deduction: float
    missing_deduction: float
    collision_deduction: float
    total_deduction: float


@dataclass
class EvalResult:
    final_score: float
    total_targets: int
    success_count: int
    missing_count: int
    timeout_count: int
    collision_count: int
    average_position_error: Optional[float]
    average_yaw_error: Optional[float]
    average_pitch_error: Optional[float]
    score_detail: ScoreDetail
    target_results: List[TargetResult]
