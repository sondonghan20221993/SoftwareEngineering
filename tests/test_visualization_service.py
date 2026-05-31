from pathlib import Path

import matplotlib.pyplot as plt
import pytest

from drone_eval.model.result import EvalResult, ScoreDetail, TargetResult
from drone_eval.service.visualization_service import VisualizationService


def _make_result(
    targets: list[TargetResult] | None = None,
    success: int = 2,
    missing: int = 1,
    collision: int = 0,
    timeout: int = 0,
    score: float = 80.0,
) -> EvalResult:
    if targets is None:
        targets = [
            TargetResult("T1", position_error=1.0, yaw_error=5.0, pitch_error=3.0,
                         position_ok=True, direction_ok=True, time_ok=True,
                         is_missing=False, position_deduction=0.0, direction_deduction=0.0,
                         timeout_deduction=0.0),
            TargetResult("T2", position_error=3.5, yaw_error=15.0, pitch_error=8.0,
                         position_ok=False, direction_ok=False, time_ok=True,
                         is_missing=False, position_deduction=7.5, direction_deduction=10.0,
                         timeout_deduction=0.0),
            TargetResult("T3", is_missing=True, position_deduction=0.0,
                         direction_deduction=0.0, timeout_deduction=0.0),
        ]
    detail = ScoreDetail(
        total_position_deduction=7.5,
        total_direction_deduction=10.0,
        total_missing_deduction=10.0,
        total_collision_deduction=0.0,
        total_timeout_deduction=0.0,
        total_deduction=27.5,
        base_score=100.0,
    )
    return EvalResult(
        mission_id="m001",
        final_score=score,
        total_targets=3,
        success_count=success,
        missing_count=missing,
        collision_count=collision,
        timeout_count=timeout,
        avg_position_error=2.25,
        avg_yaw_error=10.0,
        avg_pitch_error=5.5,
        score_detail=detail,
        target_results=targets,
    )


class TestPositionErrorFigure:
    def test_returns_figure(self):
        fig = VisualizationService.position_error_figure(_make_result())
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_missing_targets_shown_as_zero(self):
        result = _make_result()
        fig = VisualizationService.position_error_figure(result)
        assert fig is not None
        plt.close(fig)

    def test_single_target(self):
        t = TargetResult("T1", position_error=0.5, is_missing=False,
                         position_deduction=0.0, direction_deduction=0.0, timeout_deduction=0.0)
        result = _make_result(targets=[t], success=1, missing=0)
        fig = VisualizationService.position_error_figure(result)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)


class TestDirectionErrorFigure:
    def test_returns_figure(self):
        fig = VisualizationService.direction_error_figure(_make_result())
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_missing_target_errors_default_to_zero(self):
        result = _make_result()
        fig = VisualizationService.direction_error_figure(result)
        assert fig is not None
        plt.close(fig)


class TestDeductionBreakdownFigure:
    def test_returns_figure_with_score_detail(self):
        fig = VisualizationService.deduction_breakdown_figure(_make_result())
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_returns_figure_without_score_detail(self):
        result = _make_result()
        result.score_detail = None
        fig = VisualizationService.deduction_breakdown_figure(result)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)


class TestSummaryFigure:
    def test_returns_figure(self):
        fig = VisualizationService.summary_figure(_make_result())
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_all_zero_counts_does_not_raise(self):
        result = _make_result(success=0, missing=0, collision=0, timeout=0)
        fig = VisualizationService.summary_figure(result)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_high_score_result(self):
        result = _make_result(score=100.0)
        fig = VisualizationService.summary_figure(result)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)


class TestSaveFigure:
    def test_creates_png_file(self, tmp_path):
        result = _make_result()
        fig = VisualizationService.position_error_figure(result)
        out = tmp_path / "test_chart.png"
        VisualizationService.save_figure(fig, out)
        assert out.exists()
        assert out.stat().st_size > 0

    def test_save_figure_accepts_string_path(self, tmp_path):
        result = _make_result()
        fig = VisualizationService.position_error_figure(result)
        out = str(tmp_path / "chart.png")
        VisualizationService.save_figure(fig, out)
        assert Path(out).exists()


class TestSaveAll:
    def test_creates_four_chart_files(self, tmp_path):
        result = _make_result()
        saved = VisualizationService.save_all(result, tmp_path)
        assert len(saved) == 4
        for path in saved:
            assert Path(path).exists()

    def test_creates_output_directory_if_missing(self, tmp_path):
        result = _make_result()
        out_dir = tmp_path / "new_charts"
        VisualizationService.save_all(result, out_dir)
        assert out_dir.exists()

    def test_saved_files_are_named_correctly(self, tmp_path):
        result = _make_result()
        saved = VisualizationService.save_all(result, tmp_path)
        names = {Path(p).name for p in saved}
        assert "chart_position_error.png" in names
        assert "chart_direction_error.png" in names
        assert "chart_deduction.png" in names
        assert "chart_summary.png" in names

    def test_with_mission_creates_six_files(self, tmp_path):
        from drone_eval.model.mission import MissionConfig, ScorePolicy, TargetPoint
        mission = MissionConfig(
            mission_id="m1",
            allow_position_error=2.0,
            allow_yaw_error=10.0,
            allow_pitch_error=10.0,
            targets=[TargetPoint("T1", 0.0, 0.0, -10.0, 90.0, -30.0, 60.0)],
            score_policy=ScorePolicy(5.0, 2.0, 2.0, 10.0, 20.0, 5.0, 1.0, 1.0),
        )
        result = _make_result()
        result.mission_start_time = 1.0
        saved = VisualizationService.save_all(result, tmp_path, mission=mission)
        assert len(saved) == 6
        names = {Path(p).name for p in saved}
        assert "chart_position_scatter.png" in names
        assert "chart_capture_timeline.png" in names


class TestPositionScatterFigure:
    @pytest.fixture
    def mission(self):
        from drone_eval.model.mission import MissionConfig, ScorePolicy, TargetPoint
        return MissionConfig(
            mission_id="m1",
            allow_position_error=2.0,
            allow_yaw_error=10.0,
            allow_pitch_error=10.0,
            targets=[
                TargetPoint("T1", 0.0, 0.0, -10.0, 90.0, -30.0, 60.0),
                TargetPoint("T2", 20.0, 0.0, -10.0, 0.0, -20.0, 30.0),
                TargetPoint("T3", 10.0, 10.0, -10.0, 45.0, -25.0, 45.0),
            ],
            score_policy=ScorePolicy(5.0, 2.0, 2.0, 10.0, 20.0, 5.0, 1.0, 1.0),
        )

    def test_returns_figure(self, mission):
        result = _make_result()
        fig = VisualizationService.position_scatter_figure(result, mission)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_missing_target_in_map_does_not_raise(self, mission):
        result = _make_result()
        mission.targets = mission.targets[:1]
        fig = VisualizationService.position_scatter_figure(result, mission)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_all_missing_targets(self, mission):
        targets = [
            TargetResult("T1", is_missing=True, position_deduction=0.0,
                         direction_deduction=0.0, timeout_deduction=0.0),
            TargetResult("T2", is_missing=True, position_deduction=0.0,
                         direction_deduction=0.0, timeout_deduction=0.0),
        ]
        result = _make_result(targets=targets, success=0, missing=2)
        fig = VisualizationService.position_scatter_figure(result, mission)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)


class TestCaptureTimelineFigure:
    @pytest.fixture
    def mission(self):
        from drone_eval.model.mission import MissionConfig, ScorePolicy, TargetPoint
        return MissionConfig(
            mission_id="m1",
            allow_position_error=2.0,
            allow_yaw_error=10.0,
            allow_pitch_error=10.0,
            targets=[
                TargetPoint("T1", 0.0, 0.0, -10.0, 90.0, -30.0, 60.0),
                TargetPoint("T2", 20.0, 0.0, -10.0, 0.0, -20.0, 30.0),
                TargetPoint("T3", 10.0, 10.0, -10.0, 45.0, -25.0, 45.0),
            ],
            score_policy=ScorePolicy(5.0, 2.0, 2.0, 10.0, 20.0, 5.0, 1.0, 1.0),
        )

    def test_returns_figure(self, mission):
        result = _make_result()
        result.mission_start_time = 1.0
        fig = VisualizationService.capture_timeline_figure(result, mission)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_no_mission_start_time(self, mission):
        result = _make_result()
        result.mission_start_time = None
        fig = VisualizationService.capture_timeline_figure(result, mission)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_all_missing_targets(self, mission):
        targets = [
            TargetResult("T1", is_missing=True, position_deduction=0.0,
                         direction_deduction=0.0, timeout_deduction=0.0),
        ]
        result = _make_result(targets=targets, success=0, missing=1)
        result.mission_start_time = 0.0
        fig = VisualizationService.capture_timeline_figure(result, mission)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_timeout_target_shown(self, mission):
        from drone_eval.model.logs import CaptureRecord
        cap = CaptureRecord(100.0, 0.0, 0.0, -10.0, 0.0, -30.0, 90.0, "img.png")
        targets = [
            TargetResult("T1", matched_capture=cap, matched_capture_timestamp=100.0,
                         position_ok=True, direction_ok=True, time_ok=False,
                         is_missing=False, is_timeout=True,
                         position_deduction=0.0, direction_deduction=0.0, timeout_deduction=5.0),
        ]
        result = _make_result(targets=targets, success=0, missing=0, timeout=1)
        result.mission_start_time = 1.0
        fig = VisualizationService.capture_timeline_figure(result, mission)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)
