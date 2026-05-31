from __future__ import annotations

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QProgressBar,
    QLabel, QTextEdit, QGroupBox
)
from PyQt5.QtCore import pyqtSignal, QThread, pyqtSlot, QObject

from drone_eval.controller.app_controller import AppController
from drone_eval.utils.exceptions import DroneEvalError


class _EvalWorker(QObject):
    progress = pyqtSignal(str, str, int)
    finished = pyqtSignal(bool, str)

    def __init__(self, controller: AppController) -> None:
        super().__init__()
        self._controller = controller

    @pyqtSlot()
    def run(self) -> None:
        try:
            self._controller.run_evaluation(
                progress=lambda stage, msg, pct: self.progress.emit(stage, msg, pct)
            )
            self.finished.emit(True, "")
        except DroneEvalError as exc:
            self.finished.emit(False, str(exc))
        except Exception as exc:
            self.finished.emit(False, f"예상치 못한 오류: {exc}")


class TabRun(QWidget):
    evaluation_finished = pyqtSignal(bool, str)

    _STAGES = ["파일 로드", "입력 검증", "매칭 및 평가", "결과 준비"]

    def __init__(self, controller: AppController, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._controller = controller
        self._thread: QThread | None = None
        self._worker: _EvalWorker | None = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        self._start_btn = QPushButton("평가 시작")
        self._start_btn.setFixedHeight(40)
        self._start_btn.clicked.connect(self._start_evaluation)
        layout.addWidget(self._start_btn)

        stage_group = QGroupBox("진행 단계")
        stage_layout = QVBoxLayout()
        self._stage_bars: dict[str, QProgressBar] = {}
        for stage in self._STAGES:
            row_label = QLabel(stage)
            bar = QProgressBar()
            bar.setRange(0, 100)
            bar.setValue(0)
            bar.setFormat(f"{stage}: %p%")
            stage_layout.addWidget(bar)
            self._stage_bars[stage] = bar
        stage_group.setLayout(stage_layout)
        layout.addWidget(stage_group)

        self._status_label = QLabel("대기 중...")
        layout.addWidget(self._status_label)

        log_group = QGroupBox("상태 로그")
        log_layout = QVBoxLayout()
        self._log_box = QTextEdit()
        self._log_box.setReadOnly(True)
        self._log_box.setMaximumHeight(150)
        log_layout.addWidget(self._log_box)
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)
        layout.addStretch()

    def _start_evaluation(self) -> None:
        if not self._controller.file_state.is_ready():
            self._status_label.setText("필수 파일이 모두 선택되지 않았습니다.")
            return

        self._start_btn.setEnabled(False)
        for bar in self._stage_bars.values():
            bar.setValue(0)
        self._log_box.clear()
        self._status_label.setText("평가 중...")

        self._thread = QThread()
        self._worker = _EvalWorker(self._controller)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_finished)
        self._worker.finished.connect(self._thread.quit)
        self._thread.start()

    @pyqtSlot(str, str, int)
    def _on_progress(self, stage: str, message: str, pct: int) -> None:
        self._status_label.setText(message)
        self._log_box.append(f"[{stage}] {message}")
        if stage in self._stage_bars:
            self._stage_bars[stage].setValue(pct)

    @pyqtSlot(bool, str)
    def _on_finished(self, success: bool, message: str) -> None:
        self._start_btn.setEnabled(True)
        if success:
            for bar in self._stage_bars.values():
                bar.setValue(100)
            self._status_label.setText("평가 완료!")
            self._log_box.append("평가가 성공적으로 완료되었습니다.")
        else:
            self._status_label.setText(f"오류: {message}")
            self._log_box.append(f"[오류] {message}")
        self.evaluation_finished.emit(success, message)
