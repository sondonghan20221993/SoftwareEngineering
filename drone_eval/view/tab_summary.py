from __future__ import annotations

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QGroupBox, QHeaderView
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from drone_eval.controller.app_controller import AppController


class TabSummary(QWidget):
    def __init__(self, controller: AppController, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._controller = controller
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        score_group = QGroupBox("최종 점수")
        score_layout = QVBoxLayout()
        self._score_label = QLabel("- / 100")
        font = QFont()
        font.setPointSize(28)
        font.setBold(True)
        self._score_label.setFont(font)
        self._score_label.setAlignment(Qt.AlignCenter)
        score_layout.addWidget(self._score_label)
        score_group.setLayout(score_layout)
        layout.addWidget(score_group)

        summary_group = QGroupBox("요약")
        summary_layout = QVBoxLayout()
        self._summary_table = QTableWidget()
        self._summary_table.setColumnCount(2)
        self._summary_table.setHorizontalHeaderLabels(["항목", "값"])
        self._summary_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._summary_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._summary_table.setSelectionMode(QTableWidget.NoSelection)
        summary_layout.addWidget(self._summary_table)
        summary_group.setLayout(summary_layout)
        layout.addWidget(summary_group)

    def refresh(self) -> None:
        result = self._controller.eval_result
        if result is None:
            self._score_label.setText("- / 100")
            self._summary_table.setRowCount(0)
            return

        self._score_label.setText(f"{result.final_score:.1f} / 100")

        sd = result.score_detail
        rows = [
            ("총 목표 수", str(result.total_targets)),
            ("성공 수", str(result.success_count)),
            ("누락 수", str(result.missing_count)),
            ("충돌 수", str(result.collision_count)),
            ("시간 초과 수", str(result.timeout_count)),
        ]
        if sd:
            rows += [
                ("총 위치 감점", f"{sd.total_position_deduction:.2f}"),
                ("총 방향 감점", f"{sd.total_direction_deduction:.2f}"),
                ("총 누락 감점", f"{sd.total_missing_deduction:.2f}"),
                ("총 충돌 감점", f"{sd.total_collision_deduction:.2f}"),
                ("총 시간 감점", f"{sd.total_timeout_deduction:.2f}"),
                ("총 감점", f"{sd.total_deduction:.2f}"),
            ]
        if result.avg_position_error is not None:
            rows.append(("평균 위치 오차", f"{result.avg_position_error:.3f} m"))
        if result.avg_yaw_error is not None:
            rows.append(("평균 Yaw 오차", f"{result.avg_yaw_error:.2f} deg"))
        if result.avg_pitch_error is not None:
            rows.append(("평균 Pitch 오차", f"{result.avg_pitch_error:.2f} deg"))

        self._summary_table.setRowCount(len(rows))
        for i, (key, val) in enumerate(rows):
            self._summary_table.setItem(i, 0, QTableWidgetItem(key))
            item = QTableWidgetItem(val)
            item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self._summary_table.setItem(i, 1, item)
