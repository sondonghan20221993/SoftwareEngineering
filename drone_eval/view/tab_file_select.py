from __future__ import annotations

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFileDialog, QTextEdit, QGroupBox, QGridLayout
)
from PyQt5.QtCore import pyqtSignal

from drone_eval.controller.app_controller import AppController
from drone_eval.utils.exceptions import FileLoadError


class TabFileSelect(QWidget):
    files_changed = pyqtSignal()

    def __init__(self, controller: AppController, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._controller = controller
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        group = QGroupBox("입력 파일 선택")
        grid = QGridLayout()

        self._fields: dict[str, QLineEdit] = {}
        rows = [
            ("임무 설정 파일", "mission_path", False),
            ("비행 로그", "flight_path", False),
            ("촬영 로그", "capture_path", False),
            ("충돌 로그", "collision_path", False),
            ("이미지 폴더 (선택)", "image_folder", True),
        ]
        for row_idx, (label_text, field_name, is_folder) in enumerate(rows):
            label = QLabel(label_text)
            edit = QLineEdit()
            edit.setReadOnly(True)
            edit.setPlaceholderText("경로를 선택하세요...")
            browse_btn = QPushButton("찾아보기")
            browse_btn.clicked.connect(
                lambda checked, fn=field_name, folder=is_folder: self._browse(fn, folder)
            )
            grid.addWidget(label, row_idx, 0)
            grid.addWidget(edit, row_idx, 1)
            grid.addWidget(browse_btn, row_idx, 2)
            self._fields[field_name] = edit

        group.setLayout(grid)
        layout.addWidget(group)

        error_group = QGroupBox("오류 메시지")
        error_layout = QVBoxLayout()
        self._error_box = QTextEdit()
        self._error_box.setReadOnly(True)
        self._error_box.setMaximumHeight(120)
        self._error_box.setPlaceholderText("파일 선택 오류가 있으면 여기에 표시됩니다.")
        error_layout.addWidget(self._error_box)
        error_group.setLayout(error_layout)
        layout.addWidget(error_group)
        layout.addStretch()

    def _browse(self, field_name: str, is_folder: bool) -> None:
        if is_folder:
            path = QFileDialog.getExistingDirectory(self, "폴더 선택")
        else:
            path, _ = QFileDialog.getOpenFileName(
                self, "파일 선택", "",
                "지원 파일 (*.json *.csv);;JSON (*.json);;CSV (*.csv);;모든 파일 (*)"
            )
        if not path:
            return

        self._fields[field_name].setText(path)
        self._controller.set_file(field_name, path)

        if field_name == "mission_path":
            self._try_load_mission(path)

        self.files_changed.emit()

    def _try_load_mission(self, path: str) -> None:
        self._error_box.clear()
        try:
            self._controller.load_mission_config()
        except FileLoadError as exc:
            self._error_box.setPlainText(f"임무 설정 로드 오류: {exc.reason}")
        except Exception as exc:
            self._error_box.setPlainText(f"오류: {exc}")

    def show_error(self, message: str) -> None:
        self._error_box.setPlainText(message)
