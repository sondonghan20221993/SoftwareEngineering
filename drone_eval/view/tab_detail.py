from __future__ import annotations

from pathlib import Path

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QTableWidget, QTableWidgetItem, QLabel, QGroupBox, QHeaderView
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QColor

from drone_eval.controller.app_controller import AppController


_OK_COLOR = QColor("#c8f7c5")
_FAIL_COLOR = QColor("#f7c5c5")
_MISSING_COLOR = QColor("#e0e0e0")


class TabDetail(QWidget):
    def __init__(self, controller: AppController, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._controller = controller
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        splitter = QSplitter(Qt.Vertical)

        table_widget = QWidget()
        table_layout = QVBoxLayout(table_widget)
        self._table = QTableWidget()
        self._table.setColumnCount(11)
        self._table.setHorizontalHeaderLabels([
            "목표ID", "매칭시각", "위치오차(m)", "Yaw오차(°)", "Pitch오차(°)",
            "위치판정", "방향판정", "시간판정", "성공", "누락", "이미지"
        ])
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self._table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectRows)
        self._table.currentCellChanged.connect(lambda row, col, prev_row, prev_col: self._on_row_changed(row))
        table_layout.addWidget(self._table)
        splitter.addWidget(table_widget)

        preview_group = QGroupBox("촬영 이미지 미리보기")
        preview_layout = QVBoxLayout()
        self._preview_label = QLabel("행을 선택하면 이미지가 표시됩니다.")
        self._preview_label.setAlignment(Qt.AlignCenter)
        self._preview_label.setMinimumHeight(200)
        self._preview_label.setStyleSheet("border: 1px solid #aaa; background: #f5f5f5;")
        preview_layout.addWidget(self._preview_label)
        preview_group.setLayout(preview_layout)
        splitter.addWidget(preview_group)

        splitter.setSizes([400, 200])
        layout.addWidget(splitter)

    def refresh(self) -> None:
        result = self._controller.eval_result
        if result is None:
            self._table.setRowCount(0)
            return

        self._table.setRowCount(len(result.target_results))
        for row, t in enumerate(result.target_results):
            def item(text: str) -> QTableWidgetItem:
                it = QTableWidgetItem(text)
                it.setTextAlignment(Qt.AlignCenter)
                return it

            ts = f"{t.matched_capture_timestamp:.2f}" if t.matched_capture_timestamp is not None else "-"
            pos_err = f"{t.position_error:.3f}" if t.position_error is not None else "-"
            yaw_err = f"{t.yaw_error:.2f}" if t.yaw_error is not None else "-"
            pitch_err = f"{t.pitch_error:.2f}" if t.pitch_error is not None else "-"

            self._table.setItem(row, 0, item(t.target_id))
            self._table.setItem(row, 1, item(ts))
            self._table.setItem(row, 2, item(pos_err))
            self._table.setItem(row, 3, item(yaw_err))
            self._table.setItem(row, 4, item(pitch_err))
            self._table.setItem(row, 5, item("O" if t.position_ok else "X"))
            self._table.setItem(row, 6, item("O" if t.direction_ok else "X"))
            self._table.setItem(row, 7, item("O" if t.time_ok else "X"))
            self._table.setItem(row, 8, item("O" if (t.position_ok and t.direction_ok and t.time_ok and not t.is_missing) else "X"))
            self._table.setItem(row, 9, item("O" if t.is_missing else "-"))
            self._table.setItem(row, 10, item("O" if t.image_linked else "X"))

            if t.is_missing:
                bg = _MISSING_COLOR
            elif t.position_ok and t.direction_ok and t.time_ok:
                bg = _OK_COLOR
            else:
                bg = _FAIL_COLOR
            for col in range(11):
                cell = self._table.item(row, col)
                if cell:
                    cell.setBackground(bg)

        self._preview_label.setText("행을 선택하면 이미지가 표시됩니다.")

    def _on_row_changed(self, row: int) -> None:
        result = self._controller.eval_result
        if result is None or row < 0 or row >= len(result.target_results):
            return

        target = result.target_results[row]
        if target.matched_capture is None or not target.image_linked:
            self._preview_label.setText("이미지 없음 또는 파일을 찾을 수 없습니다.")
            return

        image_path = target.matched_capture.image_path
        pixmap = QPixmap(image_path)
        if pixmap.isNull():
            self._preview_label.setText(f"이미지를 열 수 없습니다:\n{image_path}")
        else:
            scaled = pixmap.scaled(
                self._preview_label.width(), self._preview_label.height(),
                Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            self._preview_label.setPixmap(scaled)
