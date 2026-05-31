from __future__ import annotations

from dataclasses import dataclass, fields
from pathlib import Path
from typing import Any

from drone_eval.model.logs import CaptureRecord, CollisionRecord, FlightRecord


@dataclass
class PreviewTable:
    headers: list[str]
    rows: list[list[Any]]
    error_row_indices: list[int]


class PreviewService:
    @staticmethod
    def flight_preview(records: list[FlightRecord], validation_errors: list[str]) -> PreviewTable:
        headers = ["#", "timestamp", "x", "y", "z", "roll", "pitch", "yaw", "speed"]
        rows = []
        for i, rec in enumerate(records):
            rows.append([i, rec.timestamp, rec.x, rec.y, rec.z,
                         rec.roll, rec.pitch, rec.yaw, rec.speed])
        error_indices = PreviewService._error_indices(validation_errors, "flight", len(records))
        return PreviewTable(headers=headers, rows=rows, error_row_indices=error_indices)

    @staticmethod
    def capture_preview(records: list[CaptureRecord], validation_errors: list[str]) -> PreviewTable:
        headers = ["#", "timestamp", "x", "y", "z", "roll", "pitch", "yaw", "image_path", "file_exists"]
        rows = []
        for i, rec in enumerate(records):
            exists = Path(rec.image_path).is_file() if rec.image_path else False
            rows.append([i, rec.timestamp, rec.x, rec.y, rec.z,
                         rec.roll, rec.pitch, rec.yaw, rec.image_path, "O" if exists else "X"])
        error_indices = PreviewService._error_indices(validation_errors, "capture", len(records))
        return PreviewTable(headers=headers, rows=rows, error_row_indices=error_indices)

    @staticmethod
    def collision_preview(records: list[CollisionRecord], validation_errors: list[str]) -> PreviewTable:
        headers = ["#", "timestamp", "collision", "x", "y", "z"]
        rows = []
        for i, rec in enumerate(records):
            rows.append([i, rec.timestamp, rec.collision, rec.x, rec.y, rec.z])
        error_indices = PreviewService._error_indices(validation_errors, "collision", len(records))
        return PreviewTable(headers=headers, rows=rows, error_row_indices=error_indices)

    @staticmethod
    def _error_indices(errors: list[str], record_type: str, count: int) -> list[int]:
        indices: set[int] = set()
        prefix = f"{record_type} record "
        for err in errors:
            if err.startswith(prefix):
                rest = err[len(prefix):]
                idx_str = rest.split(":")[0].strip()
                try:
                    indices.add(int(idx_str))
                except ValueError:
                    pass
        return sorted(i for i in indices if 0 <= i < count)
