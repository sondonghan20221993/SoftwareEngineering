from __future__ import annotations

import io

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QLabel, QPushButton, QFileDialog, QScrollArea
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QImage

from drone_eval.controller.app_controller import AppController
from drone_eval.service.visualization_service import VisualizationService


def _figure_to_pixmap(fig) -> QPixmap:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=120, bbox_inches="tight")
    buf.seek(0)
    img = QImage.fromData(buf.read())
    return QPixmap.fromImage(img)


class _ChartLabel(QLabel):
    def __init__(self) -> None:
        super().__init__("평가 결과가 없습니다.")
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumSize(400, 300)
        self.setStyleSheet("background: #f5f5f5; border: 1px solid #ccc;")

    def set_figure(self, fig) -> None:
        import matplotlib.pyplot as plt
        pixmap = _figure_to_pixmap(fig)
        plt.close(fig)
        self.setPixmap(pixmap.scaled(
            self.width(), self.height(),
            Qt.KeepAspectRatio, Qt.SmoothTransformation
        ))


class TabVisual(QWidget):
    def __init__(self, controller: AppController, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._controller = controller
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        btn_row = QHBoxLayout()
        self._save_btn = QPushButton("차트 저장 (PNG)")
        self._save_btn.setEnabled(False)
        self._save_btn.clicked.connect(self._save_charts)
        btn_row.addStretch()
        btn_row.addWidget(self._save_btn)
        layout.addLayout(btn_row)

        self._chart_tabs = QTabWidget()
        self._chart_labels: dict[str, _ChartLabel] = {}
        chart_names = ["위치 오차", "방향 오차", "감점 분포", "임무 요약", "위치 분포", "촬영 타임라인"]
        for name in chart_names:
            label = _ChartLabel()
            scroll = QScrollArea()
            scroll.setWidget(label)
            scroll.setWidgetResizable(True)
            self._chart_tabs.addTab(scroll, name)
            self._chart_labels[name] = label

        layout.addWidget(self._chart_tabs)

    def refresh(self) -> None:
        result = self._controller.eval_result
        if result is None:
            return

        mission = self._controller.mission

        builders = {
            "위치 오차": lambda r: VisualizationService.position_error_figure(r),
            "방향 오차": lambda r: VisualizationService.direction_error_figure(r),
            "감점 분포": lambda r: VisualizationService.deduction_breakdown_figure(r),
            "임무 요약": lambda r: VisualizationService.summary_figure(r),
        }
        for name, builder in builders.items():
            try:
                fig = builder(result)
                self._chart_labels[name].set_figure(fig)
            except Exception:
                self._chart_labels[name].setText(f"{name} 차트 생성 실패")

        if mission is not None:
            for name, fn in [
                ("위치 분포", VisualizationService.position_scatter_figure),
                ("촬영 타임라인", VisualizationService.capture_timeline_figure),
            ]:
                try:
                    fig = fn(result, mission)
                    self._chart_labels[name].set_figure(fig)
                except Exception:
                    self._chart_labels[name].setText(f"{name} 차트 생성 실패")

        self._save_btn.setEnabled(True)

    def _save_charts(self) -> None:
        result = self._controller.eval_result
        if result is None:
            return
        output_dir = QFileDialog.getExistingDirectory(self, "차트 저장 폴더 선택")
        if not output_dir:
            return
        VisualizationService.save_all(result, output_dir, mission=self._controller.mission)
