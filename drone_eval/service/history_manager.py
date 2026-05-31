from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Optional

from drone_eval.model.history import HistoryEntry
from drone_eval.model.result import EvalResult
from drone_eval.utils.logger import get_logger

_log = get_logger(__name__)

_HISTORY_FILENAME = "eval_history.json"


class HistoryManager:
    def __init__(self, history_dir: str | Path) -> None:
        self._dir = Path(history_dir)
        self._dir.mkdir(parents=True, exist_ok=True)
        self._history_file = self._dir / _HISTORY_FILENAME

    def save_entry(self, result: EvalResult, saved_at: str) -> HistoryEntry:
        entry = HistoryEntry(
            entry_id=str(uuid.uuid4()),
            mission_id=result.mission_id,
            saved_at=saved_at,
            final_score=result.final_score,
            total_targets=result.total_targets,
            success_count=result.success_count,
            missing_count=result.missing_count,
            collision_count=result.collision_count,
            timeout_count=result.timeout_count,
            avg_position_error=result.avg_position_error,
            avg_yaw_error=result.avg_yaw_error,
            avg_pitch_error=result.avg_pitch_error,
            source_path=str(self._dir),
        )
        entries = self.load_all()
        entries.append(entry)
        self._write(entries)
        _log.debug("Saved history entry %s for mission %s", entry.entry_id, entry.mission_id)
        return entry

    def load_all(self) -> list[HistoryEntry]:
        if not self._history_file.exists():
            return []
        try:
            data = json.loads(self._history_file.read_text(encoding="utf-8"))
            return [HistoryEntry(**item) for item in data]
        except Exception as exc:
            _log.warning("Could not load history file: %s", exc)
            return []

    def delete_entry(self, entry_id: str) -> bool:
        entries = self.load_all()
        original_count = len(entries)
        entries = [e for e in entries if e.entry_id != entry_id]
        if len(entries) == original_count:
            return False
        self._write(entries)
        return True

    def clear_all(self) -> None:
        self._write([])

    def _write(self, entries: list[HistoryEntry]) -> None:
        payload = [
            {
                "entry_id": e.entry_id,
                "mission_id": e.mission_id,
                "saved_at": e.saved_at,
                "final_score": e.final_score,
                "total_targets": e.total_targets,
                "success_count": e.success_count,
                "missing_count": e.missing_count,
                "collision_count": e.collision_count,
                "timeout_count": e.timeout_count,
                "avg_position_error": e.avg_position_error,
                "avg_yaw_error": e.avg_yaw_error,
                "avg_pitch_error": e.avg_pitch_error,
                "source_path": e.source_path,
            }
            for e in entries
        ]
        self._history_file.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
