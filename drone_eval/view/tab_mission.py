from __future__ import annotations

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLabel, QTableWidget,
    QTableWidgetItem, QGroupBox, QHeaderView
)
from PyQt5.QtCore import Qt

from drone_eval.controller.app_controller import AppController


class TabMission(QWidget):
    def __init__(self, controller: AppController, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._controller = controller
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        info_group = QGroupBox("임무 기본 정보")
        form = QFormLayout()
        self._lbl_mission_id = QLabel("-")
        self._lbl_pos_err = QLabel("-")
        self._lbl_yaw_err = QLabel("-")
        self._lbl_pitch_err = QLabel("-")
        self._lbl_policy = QLabel("-")
        form.addRow("임무 ID:", self._lbl_mission_id)
        form.addRow("허용 위치 오차:", self._lbl_pos_err)
        form.addRow("허용 Yaw 오차:", self._lbl_yaw_err)
        form.addRow("허용 Pitch 오차:", self._lbl_pitch_err)
        form.addRow("감점 정책:", self._lbl_policy)
        info_group.setLayout(form)
        layout.addWidget(info_group)

        target_group = QGroupBox("목표 목록")
        target_layout = QVBoxLayout()
        self._target_table = QTableWidget()
        self._target_table.setColumnCount(7)
        self._target_table.setHorizontalHeaderLabels(
            ["목표ID", "X", "Y", "Z", "Yaw", "Pitch", "제한시간(s)"]
        )
        self._target_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._target_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._target_table.setSelectionBehavior(QTableWidget.SelectRows)
        target_layout.addWidget(self._target_table)
        target_group.setLayout(target_layout)
        layout.addWidget(target_group)

    def refresh(self) -> None:
        mission = self._controller.mission
        if mission is None:
            self._clear()
            return

        self._lbl_mission_id.setText(mission.mission_id)
        self._lbl_pos_err.setText(f"{mission.allow_position_error:.2f} m")
        self._lbl_yaw_err.setText(f"{mission.allow_yaw_error:.2f} deg")
        self._lbl_pitch_err.setText(f"{mission.allow_pitch_error:.2f} deg")

        sp = mission.score_policy
        policy_text = (
            f"위치 {sp.position_penalty_per_meter}/m, "
            f"Yaw {sp.direction_yaw_penalty_per_degree}/deg, "
            f"Pitch {sp.direction_pitch_penalty_per_degree}/deg, "
            f"누락 {sp.missing_capture_penalty}, "
            f"충돌 {sp.collision_penalty}, "
            f"시간초과 {sp.timeout_penalty}"
        )
        self._lbl_policy.setText(policy_text)

        self._target_table.setRowCount(len(mission.targets))
        for row, t in enumerate(mission.targets):
            self._target_table.setItem(row, 0, QTableWidgetItem(t.target_id))
            self._target_table.setItem(row, 1, QTableWidgetItem(f"{t.x:.2f}"))
            self._target_table.setItem(row, 2, QTableWidgetItem(f"{t.y:.2f}"))
            self._target_table.setItem(row, 3, QTableWidgetItem(f"{t.z:.2f}"))
            self._target_table.setItem(row, 4, QTableWidgetItem(f"{t.yaw:.2f}"))
            self._target_table.setItem(row, 5, QTableWidgetItem(f"{t.pitch:.2f}"))
            self._target_table.setItem(row, 6, QTableWidgetItem(f"{t.time_limit:.1f}"))

    def _clear(self) -> None:
        self._lbl_mission_id.setText("-")
        self._lbl_pos_err.setText("-")
        self._lbl_yaw_err.setText("-")
        self._lbl_pitch_err.setText("-")
        self._lbl_policy.setText("-")
        self._target_table.setRowCount(0)
