from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class HistoryEntry:
    entry_id: str
    mission_id: str
    saved_at: str
    final_score: float
    total_targets: int
    success_count: int
    missing_count: int
    collision_count: int
    timeout_count: int
    avg_position_error: Optional[float]
    avg_yaw_error: Optional[float]
    avg_pitch_error: Optional[float]
    source_path: str


@dataclass
class HistoryCompareRow:
    target_id: str
    entries: list[Optional[float]] = field(default_factory=list)
