from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Optional

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D
import numpy as np

from drone_eval.model.result import EvalResult

if TYPE_CHECKING:
    from drone_eval.model.mission import MissionConfig


class VisualizationService:
    @staticmethod
    def position_error_figure(result: EvalResult) -> plt.Figure:
        targets = result.target_results
        ids = [t.target_id for t in targets]
        errors = [t.position_error if t.position_error is not None else 0.0 for t in targets]
        colors = ["steelblue" if not t.is_missing else "lightgray" for t in targets]

        fig, ax = plt.subplots(figsize=(max(6, len(ids) * 0.8), 4))
        ax.bar(ids, errors, color=colors)
        ax.set_title("Position Error per Target")
        ax.set_xlabel("Target ID")
        ax.set_ylabel("Position Error (m)")
        ax.tick_params(axis="x", rotation=45)
        fig.tight_layout()
        return fig

    @staticmethod
    def direction_error_figure(result: EvalResult) -> plt.Figure:
        targets = result.target_results
        ids = [t.target_id for t in targets]
        yaw_errors = [t.yaw_error if t.yaw_error is not None else 0.0 for t in targets]
        pitch_errors = [t.pitch_error if t.pitch_error is not None else 0.0 for t in targets]

        x = np.arange(len(ids))
        width = 0.35

        fig, ax = plt.subplots(figsize=(max(6, len(ids) * 0.8), 4))
        ax.bar(x - width / 2, yaw_errors, width, label="Yaw Error", color="steelblue")
        ax.bar(x + width / 2, pitch_errors, width, label="Pitch Error", color="darkorange")
        ax.set_title("Direction Error per Target")
        ax.set_xlabel("Target ID")
        ax.set_ylabel("Direction Error (deg)")
        ax.set_xticks(x)
        ax.set_xticklabels(ids, rotation=45)
        ax.legend()
        fig.tight_layout()
        return fig

    @staticmethod
    def deduction_breakdown_figure(result: EvalResult) -> plt.Figure:
        if result.score_detail is None:
            fig, ax = plt.subplots()
            ax.text(0.5, 0.5, "No Data", ha="center", va="center")
            return fig

        sd = result.score_detail
        labels = ["Position", "Direction", "Missing", "Collision", "Timeout"]
        values = [
            sd.total_position_deduction,
            sd.total_direction_deduction,
            sd.total_missing_deduction,
            sd.total_collision_deduction,
            sd.total_timeout_deduction,
        ]
        colors = ["steelblue", "darkorange", "tomato", "crimson", "goldenrod"]

        fig, ax = plt.subplots(figsize=(6, 4))
        bars = ax.bar(labels, values, color=colors)
        for bar, val in zip(bars, values):
            if val > 0:
                ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.2,
                        f"{val:.1f}", ha="center", va="bottom", fontsize=9)
        ax.set_title("Deduction Breakdown")
        ax.set_ylabel("Deduction")
        fig.tight_layout()
        return fig

    @staticmethod
    def summary_figure(result: EvalResult) -> plt.Figure:
        labels = ["Success", "Missing", "Collision", "Timeout"]
        values = [
            result.success_count,
            result.missing_count,
            result.collision_count,
            result.timeout_count,
        ]
        colors = ["mediumseagreen", "tomato", "crimson", "goldenrod"]
        non_zero = [(l, v, c) for l, v, c in zip(labels, values, colors) if v > 0]

        fig, axes = plt.subplots(1, 2, figsize=(10, 4))

        ax_pie = axes[0]
        if non_zero:
            pie_labels, pie_vals, pie_colors = zip(*non_zero)
            ax_pie.pie(pie_vals, labels=pie_labels, colors=pie_colors,
                       autopct="%1.0f%%", startangle=90)
        else:
            ax_pie.text(0.5, 0.5, "No Data", ha="center", va="center")
        ax_pie.set_title("Mission Result Distribution")

        ax_score = axes[1]
        score = result.final_score
        color = "mediumseagreen" if score >= 80 else ("goldenrod" if score >= 60 else "tomato")
        ax_score.barh(["Final Score"], [score], color=color)
        ax_score.barh(["Final Score"], [100 - score], left=[score], color="lightgray")
        ax_score.set_xlim(0, 100)
        ax_score.set_title("Final Score")
        ax_score.text(score / 2, 0, f"{score:.1f}", ha="center", va="center",
                      color="white", fontweight="bold")

        fig.tight_layout()
        return fig

    @staticmethod
    def position_scatter_figure(result: EvalResult, mission: "MissionConfig") -> plt.Figure:
        target_map = {t.target_id: t for t in mission.targets}

        fig, ax = plt.subplots(figsize=(8, 7))

        for tr in result.target_results:
            tgt = target_map.get(tr.target_id)
            if tgt is None:
                continue

            ax.scatter(tgt.x, tgt.y, marker="x", s=120, c="crimson", zorder=5, linewidths=2)
            ax.annotate(
                tr.target_id,
                (tgt.x, tgt.y),
                textcoords="offset points",
                xytext=(6, 6),
                fontsize=8,
                color="crimson",
            )

            if not tr.is_missing and tr.matched_capture is not None:
                cap = tr.matched_capture
                success = tr.position_ok and tr.direction_ok and tr.time_ok
                color = "steelblue" if success else "darkorange"
                ax.scatter(cap.x, cap.y, marker="o", s=70, c=color, zorder=4)
                ax.plot(
                    [tgt.x, cap.x], [tgt.y, cap.y],
                    color="gray", alpha=0.4, linewidth=1, linestyle="--",
                )

        legend_elements = [
            Line2D([0], [0], marker="x", color="crimson", label="Target Position",
                   markersize=9, linestyle="None", markeredgewidth=2),
            Line2D([0], [0], marker="o", color="steelblue", label="Capture OK",
                   markersize=8, linestyle="None"),
            Line2D([0], [0], marker="o", color="darkorange", label="Capture Failed",
                   markersize=8, linestyle="None"),
        ]
        ax.legend(handles=legend_elements, loc="best")
        ax.set_title("Target vs Capture Position (Top View X-Y)")
        ax.set_xlabel("X (m)")
        ax.set_ylabel("Y (m)")
        ax.grid(True, alpha=0.3)
        ax.set_aspect("equal", adjustable="datalim")
        fig.tight_layout()
        return fig

    @staticmethod
    def capture_timeline_figure(result: EvalResult, mission: "MissionConfig") -> plt.Figure:
        target_map = {t.target_id: t for t in mission.targets}
        t_start = result.mission_start_time

        ids = [tr.target_id for tr in result.target_results]
        y_pos = list(range(len(ids)))

        fig, ax = plt.subplots(figsize=(max(8, len(ids) * 1.2), max(4, len(ids) * 0.6)))

        for y, tr in zip(y_pos, result.target_results):
            tgt = target_map.get(tr.target_id)
            time_limit = tgt.time_limit if tgt else None

            if time_limit is not None:
                ax.barh(y, time_limit, height=0.4, color="lightsteelblue",
                        alpha=0.5, label="Time Limit" if y == 0 else "")
                ax.text(time_limit, y, f" {time_limit:.0f}s",
                        va="center", fontsize=8, color="steelblue")

            if tr.is_missing:
                ax.scatter([], [], marker="D", color="lightgray")
                ax.text(0.5, y, "Missing", va="center", fontsize=8,
                        color="gray", style="italic")
                continue

            if tr.matched_capture_timestamp is not None and t_start is not None:
                elapsed = tr.matched_capture_timestamp - t_start
                color = "mediumseagreen" if tr.time_ok else "tomato"
                ax.scatter(elapsed, y, marker="D", s=80, color=color, zorder=5)
                ax.text(elapsed, y + 0.25, f"{elapsed:.1f}s",
                        ha="center", fontsize=8, color=color)

        legend_elements = [
            mpatches.Patch(facecolor="lightsteelblue", alpha=0.5, label="Time Limit"),
            Line2D([0], [0], marker="D", color="mediumseagreen", label="Capture OK (in time)",
                   markersize=8, linestyle="None"),
            Line2D([0], [0], marker="D", color="tomato", label="Timeout",
                   markersize=8, linestyle="None"),
        ]
        ax.legend(handles=legend_elements, loc="upper right")
        ax.set_yticks(y_pos)
        ax.set_yticklabels(ids)
        ax.set_xlabel("Elapsed Time from Mission Start (s)")
        ax.set_title("Capture Time vs Time Limit per Target")
        ax.grid(True, axis="x", alpha=0.3)
        fig.tight_layout()
        return fig

    @staticmethod
    def save_figure(fig: plt.Figure, path: str | Path) -> None:
        fig.savefig(str(path), dpi=150, bbox_inches="tight")
        plt.close(fig)

    @staticmethod
    def save_all(
        result: EvalResult,
        output_dir: str | Path,
        mission: "Optional[MissionConfig]" = None,
    ) -> list[str]:
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        saved: list[str] = []

        charts = {
            "chart_position_error.png": VisualizationService.position_error_figure(result),
            "chart_direction_error.png": VisualizationService.direction_error_figure(result),
            "chart_deduction.png": VisualizationService.deduction_breakdown_figure(result),
            "chart_summary.png": VisualizationService.summary_figure(result),
        }
        if mission is not None:
            charts["chart_position_scatter.png"] = VisualizationService.position_scatter_figure(result, mission)
            charts["chart_capture_timeline.png"] = VisualizationService.capture_timeline_figure(result, mission)

        for filename, fig in charts.items():
            target = out / filename
            VisualizationService.save_figure(fig, target)
            saved.append(str(target))
        return saved
