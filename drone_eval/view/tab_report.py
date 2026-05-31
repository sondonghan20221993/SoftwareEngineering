from __future__ import annotations

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QLineEdit, QPushButton, QCheckBox,
    QTextEdit, QFileDialog
)
from PyQt5.QtCore import Qt

from drone_eval.controller.app_controller import AppController, ExportConfig
from drone_eval.utils.exceptions import ExportError


class TabReport(QWidget):
    def __init__(self, controller: AppController, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._controller = controller
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        dir_group = QGroupBox("저장 폴더")
        dir_layout = QHBoxLayout()
        self._dir_edit = QLineEdit()
        self._dir_edit.setReadOnly(True)
        self._dir_edit.setPlaceholderText("저장 폴더를 선택하세요...")
        browse_btn = QPushButton("찾아보기")
        browse_btn.clicked.connect(self._browse_dir)
        dir_layout.addWidget(self._dir_edit)
        dir_layout.addWidget(browse_btn)
        dir_group.setLayout(dir_layout)
        layout.addWidget(dir_group)

        files_group = QGroupBox("저장할 파일")
        files_layout = QVBoxLayout()
        self._cb_json = QCheckBox("eval_result.json")
        self._cb_csv = QCheckBox("eval_result.csv")
        self._cb_detail = QCheckBox("eval_detail.csv")
        self._cb_summary = QCheckBox("eval_summary.json")
        for cb in (self._cb_json, self._cb_csv, self._cb_detail, self._cb_summary):
            cb.setChecked(True)
            files_layout.addWidget(cb)
        files_group.setLayout(files_layout)
        layout.addWidget(files_group)

        self._save_btn = QPushButton("리포트 저장")
        self._save_btn.setEnabled(False)
        self._save_btn.setFixedHeight(36)
        self._save_btn.clicked.connect(self._save)
        layout.addWidget(self._save_btn)

        result_group = QGroupBox("저장 결과")
        result_layout = QVBoxLayout()
        self._result_box = QTextEdit()
        self._result_box.setReadOnly(True)
        self._result_box.setMaximumHeight(150)
        result_layout.addWidget(self._result_box)
        result_group.setLayout(result_layout)
        layout.addWidget(result_group)
        layout.addStretch()

    def set_result_ready(self, ready: bool) -> None:
        self._save_btn.setEnabled(ready and bool(self._dir_edit.text()))

    def _browse_dir(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "저장 폴더 선택")
        if path:
            self._dir_edit.setText(path)
            self._save_btn.setEnabled(self._controller.eval_result is not None)

    def _save(self) -> None:
        config = ExportConfig(
            output_dir=self._dir_edit.text(),
            save_eval_result_json=self._cb_json.isChecked(),
            save_eval_result_csv=self._cb_csv.isChecked(),
            save_eval_detail_csv=self._cb_detail.isChecked(),
            save_eval_summary_json=self._cb_summary.isChecked(),
        )

        from datetime import datetime
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        try:
            save_result = self._controller.export_results(config, timestamp)
        except ExportError as exc:
            self._result_box.setPlainText(f"저장 실패:\n{exc}")
            return

        lines = []
        if save_result.saved:
            lines.append("저장 성공:")
            for path in save_result.saved:
                lines.append(f"  - {path}")
        if save_result.failed:
            lines.append("\n저장 실패:")
            for name, reason in save_result.failed:
                lines.append(f"  - {name}: {reason}")
        self._result_box.setPlainText("\n".join(lines))
