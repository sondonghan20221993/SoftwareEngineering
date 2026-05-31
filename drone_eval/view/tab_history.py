from __future__ import annotations

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QPushButton, QLabel, QMessageBox, QGroupBox,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor

from drone_eval.controller.app_controller import AppController
from drone_eval.model.history import HistoryEntry

_BEST_COLOR = QColor("#c8f7c5")
_WORST_COLOR = QColor("#f7c5c5")

_COLUMNS = [
    ("임무 ID", "mission_id"),
    ("저장 시각", "saved_at"),
    ("최종 점수", "final_score"),
    ("총 목표", "total_targets"),
    ("성공", "success_count"),
    ("누락", "missing_count"),
    ("충돌", "collision_count"),
    ("시간초과", "timeout_count"),
    ("평균 위치 오차(m)", "avg_position_error"),
    ("평균 Yaw 오차(°)", "avg_yaw_error"),
    ("평균 Pitch 오차(°)", "avg_pitch_error"),
]


class TabHistory(QWidget):
    def __init__(self, controller: AppController, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._controller = controller
        self._entries: list[HistoryEntry] = []
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        btn_row = QHBoxLayout()
        self._refresh_btn = QPushButton("새로고침")
        self._refresh_btn.clicked.connect(self.refresh)
        self._delete_btn = QPushButton("선택 항목 삭제")
        self._delete_btn.setEnabled(False)
        self._delete_btn.clicked.connect(self._delete_selected)
        self._clear_btn = QPushButton("전체 삭제")
        self._clear_btn.clicked.connect(self._clear_all)
        btn_row.addWidget(self._refresh_btn)
        btn_row.addWidget(self._delete_btn)
        btn_row.addStretch()
        btn_row.addWidget(self._clear_btn)
        layout.addLayout(btn_row)

        history_group = QGroupBox("평가 이력")
        history_layout = QVBoxLayout()
        self._table = QTableWidget()
        self._table.setColumnCount(len(_COLUMNS))
        self._table.setHorizontalHeaderLabels([col[0] for col in _COLUMNS])
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self._table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectRows)
        self._table.itemSelectionChanged.connect(self._on_selection_changed)
        history_layout.addWidget(self._table)
        history_group.setLayout(history_layout)
        layout.addWidget(history_group)

        self._status_label = QLabel("새로고침을 눌러 평가 이력을 불러오세요.")
        layout.addWidget(self._status_label)

    def refresh(self) -> None:
        self._entries = self._controller.load_history()
        self._table.setRowCount(len(self._entries))

        if not self._entries:
            self._status_label.setText("저장된 평가 이력이 없습니다.")
            return

        scores = [e.final_score for e in self._entries]
        best_score = max(scores)
        worst_score = min(scores)

        for row, entry in enumerate(self._entries):
            values = [
                entry.mission_id,
                entry.saved_at,
                f"{entry.final_score:.1f}",
                str(entry.total_targets),
                str(entry.success_count),
                str(entry.missing_count),
                str(entry.collision_count),
                str(entry.timeout_count),
                f"{entry.avg_position_error:.3f}" if entry.avg_position_error is not None else "-",
                f"{entry.avg_yaw_error:.2f}" if entry.avg_yaw_error is not None else "-",
                f"{entry.avg_pitch_error:.2f}" if entry.avg_pitch_error is not None else "-",
            ]
            for col, text in enumerate(values):
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignCenter)
                if col == 2:
                    if entry.final_score == best_score and best_score != worst_score:
                        item.setBackground(_BEST_COLOR)
                    elif entry.final_score == worst_score and best_score != worst_score:
                        item.setBackground(_WORST_COLOR)
                self._table.setItem(row, col, item)

        self._status_label.setText(f"총 {len(self._entries)}건의 평가 이력")

    def _on_selection_changed(self) -> None:
        self._delete_btn.setEnabled(bool(self._table.selectedItems()))

    def _delete_selected(self) -> None:
        rows = sorted({idx.row() for idx in self._table.selectedIndexes()}, reverse=True)
        if not rows:
            return

        reply = QMessageBox.question(
            self, "삭제 확인",
            f"{len(rows)}건의 이력을 삭제하시겠습니까?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        for row in rows:
            if row < len(self._entries):
                self._controller.delete_history_entry(self._entries[row].entry_id)

        self.refresh()

    def _clear_all(self) -> None:
        if not self._entries:
            return
        reply = QMessageBox.question(
            self, "전체 삭제 확인",
            "모든 평가 이력을 삭제하시겠습니까?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return
        self._controller.clear_history()
        self.refresh()
