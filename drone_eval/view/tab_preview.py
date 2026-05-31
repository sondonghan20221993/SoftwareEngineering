from __future__ import annotations

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QPushButton, QLabel, QGroupBox,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor

from drone_eval.controller.app_controller import AppController
from drone_eval.service.preview_service import PreviewService, PreviewTable

_ERROR_COLOR = QColor("#f7c5c5")
_WARN_COLOR = QColor("#fff3c8")


class TabPreview(QWidget):
    def __init__(self, controller: AppController, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._controller = controller
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        btn_row = QHBoxLayout()
        self._refresh_btn = QPushButton("새로고침")
        self._refresh_btn.clicked.connect(self.refresh)
        btn_row.addStretch()
        btn_row.addWidget(self._refresh_btn)
        layout.addLayout(btn_row)

        self._log_tabs = QTabWidget()

        self._flight_table = self._make_table()
        self._capture_table = self._make_table()
        self._collision_table = self._make_table()

        self._log_tabs.addTab(self._flight_table, "비행 로그")
        self._log_tabs.addTab(self._capture_table, "촬영 로그")
        self._log_tabs.addTab(self._collision_table, "충돌 로그")

        layout.addWidget(self._log_tabs)

        error_group = QGroupBox("검증 오류 목록")
        error_layout = QVBoxLayout()
        self._error_table = QTableWidget()
        self._error_table.setColumnCount(1)
        self._error_table.setHorizontalHeaderLabels(["오류 내용"])
        self._error_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._error_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._error_table.setMaximumHeight(130)
        error_layout.addWidget(self._error_table)
        error_group.setLayout(error_layout)
        layout.addWidget(error_group)

        self._status_label = QLabel("평가를 실행하면 로그 데이터가 표시됩니다.")
        layout.addWidget(self._status_label)

    def _make_table(self) -> QTableWidget:
        table = QTableWidget()
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        return table

    def _populate(self, table: QTableWidget, preview: PreviewTable) -> None:
        table.setColumnCount(len(preview.headers))
        table.setHorizontalHeaderLabels(preview.headers)
        table.setRowCount(len(preview.rows))
        error_set = set(preview.error_row_indices)
        for row_idx, row in enumerate(preview.rows):
            for col_idx, value in enumerate(row):
                text = "" if value is None else str(value)
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignCenter)
                if row_idx in error_set:
                    item.setBackground(_ERROR_COLOR)
                table.setItem(row_idx, col_idx, item)

    def _populate_errors(self, errors: list[str]) -> None:
        self._error_table.setRowCount(len(errors))
        for i, msg in enumerate(errors):
            item = QTableWidgetItem(msg)
            item.setBackground(_WARN_COLOR)
            self._error_table.setItem(i, 0, item)

    def refresh(self) -> None:
        errors = self._controller.validation_errors

        flight = self._controller.flight_records
        if flight:
            self._populate(self._flight_table, PreviewService.flight_preview(flight, errors))
            self._log_tabs.setTabText(0, f"비행 로그 ({len(flight)}건)")
        else:
            self._flight_table.setRowCount(0)
            self._log_tabs.setTabText(0, "비행 로그")

        capture = self._controller.capture_records
        if capture:
            self._populate(self._capture_table, PreviewService.capture_preview(capture, errors))
            self._log_tabs.setTabText(1, f"촬영 로그 ({len(capture)}건)")
        else:
            self._capture_table.setRowCount(0)
            self._log_tabs.setTabText(1, "촬영 로그")

        collision = self._controller.collision_records
        if collision:
            self._populate(self._collision_table, PreviewService.collision_preview(collision, errors))
            self._log_tabs.setTabText(2, f"충돌 로그 ({len(collision)}건)")
        else:
            self._collision_table.setRowCount(0)
            self._log_tabs.setTabText(2, "충돌 로그")

        self._populate_errors(errors)

        total = len(flight) + len(capture) + len(collision)
        if total:
            self._status_label.setText(
                f"총 {total}건 로드됨 | 검증 오류: {len(errors)}건"
            )
        else:
            self._status_label.setText("로드된 로그 데이터가 없습니다.")
