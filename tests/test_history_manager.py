from pathlib import Path

import pytest

from drone_eval.model.result import EvalResult, ScoreDetail
from drone_eval.service.history_manager import HistoryManager


def _make_result(score: float = 85.0, mission_id: str = "mission_001") -> EvalResult:
    return EvalResult(
        mission_id=mission_id,
        final_score=score,
        total_targets=3,
        success_count=2,
        missing_count=1,
        collision_count=0,
        timeout_count=0,
        avg_position_error=1.2,
        avg_yaw_error=5.0,
        avg_pitch_error=3.0,
        score_detail=ScoreDetail(
            total_position_deduction=3.0,
            total_direction_deduction=2.0,
            total_missing_deduction=10.0,
            total_collision_deduction=0.0,
            total_timeout_deduction=0.0,
            total_deduction=15.0,
            base_score=100.0,
        ),
    )


@pytest.fixture
def manager(tmp_path: Path) -> HistoryManager:
    return HistoryManager(tmp_path / "history")


class TestSaveEntry:
    def test_returns_entry_with_correct_mission_id(self, manager):
        result = _make_result()
        entry = manager.save_entry(result, "2026-05-31 10:00:00")
        assert entry.mission_id == "mission_001"

    def test_returns_entry_with_correct_score(self, manager):
        result = _make_result(score=72.5)
        entry = manager.save_entry(result, "2026-05-31 10:00:00")
        assert entry.final_score == 72.5

    def test_entry_id_is_unique_per_save(self, manager):
        result = _make_result()
        e1 = manager.save_entry(result, "2026-05-31 10:00:00")
        e2 = manager.save_entry(result, "2026-05-31 10:01:00")
        assert e1.entry_id != e2.entry_id

    def test_creates_history_file(self, manager, tmp_path):
        manager.save_entry(_make_result(), "2026-05-31 10:00:00")
        history_file = tmp_path / "history" / "eval_history.json"
        assert history_file.exists()

    def test_saved_at_preserved(self, manager):
        entry = manager.save_entry(_make_result(), "2026-05-31 12:34:56")
        assert entry.saved_at == "2026-05-31 12:34:56"


class TestLoadAll:
    def test_returns_empty_list_when_no_file(self, manager):
        assert manager.load_all() == []

    def test_returns_saved_entries(self, manager):
        manager.save_entry(_make_result(), "2026-05-31 10:00:00")
        manager.save_entry(_make_result(score=90.0), "2026-05-31 10:01:00")
        entries = manager.load_all()
        assert len(entries) == 2

    def test_entries_preserve_score(self, manager):
        manager.save_entry(_make_result(score=77.0), "2026-05-31 10:00:00")
        entries = manager.load_all()
        assert entries[0].final_score == 77.0

    def test_entries_preserve_counts(self, manager):
        manager.save_entry(_make_result(), "2026-05-31 10:00:00")
        entries = manager.load_all()
        assert entries[0].total_targets == 3
        assert entries[0].success_count == 2
        assert entries[0].missing_count == 1

    def test_corrupt_file_returns_empty(self, tmp_path):
        history_dir = tmp_path / "history"
        history_dir.mkdir()
        (history_dir / "eval_history.json").write_text("not valid json", encoding="utf-8")
        manager = HistoryManager(history_dir)
        assert manager.load_all() == []


class TestDeleteEntry:
    def test_delete_removes_entry(self, manager):
        entry = manager.save_entry(_make_result(), "2026-05-31 10:00:00")
        deleted = manager.delete_entry(entry.entry_id)
        assert deleted is True
        assert manager.load_all() == []

    def test_delete_nonexistent_returns_false(self, manager):
        assert manager.delete_entry("no-such-id") is False

    def test_delete_only_removes_target_entry(self, manager):
        e1 = manager.save_entry(_make_result(), "2026-05-31 10:00:00")
        manager.save_entry(_make_result(score=90.0), "2026-05-31 10:01:00")
        manager.delete_entry(e1.entry_id)
        remaining = manager.load_all()
        assert len(remaining) == 1
        assert remaining[0].final_score == 90.0


class TestClearAll:
    def test_clear_removes_all_entries(self, manager):
        manager.save_entry(_make_result(), "2026-05-31 10:00:00")
        manager.save_entry(_make_result(), "2026-05-31 10:01:00")
        manager.clear_all()
        assert manager.load_all() == []

    def test_clear_on_empty_history_does_not_fail(self, manager):
        manager.clear_all()
        assert manager.load_all() == []

    def test_save_after_clear_works(self, manager):
        manager.save_entry(_make_result(), "2026-05-31 10:00:00")
        manager.clear_all()
        manager.save_entry(_make_result(score=60.0), "2026-05-31 10:02:00")
        entries = manager.load_all()
        assert len(entries) == 1
        assert entries[0].final_score == 60.0
