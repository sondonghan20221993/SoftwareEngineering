from __future__ import annotations

from PyQt5.QtWidgets import (
    QMainWindow, QTabWidget, QStatusBar, QWidget, QVBoxLayout, QLabel
)
from PyQt5.QtCore import Qt

from drone_eval.controller.app_controller import AppController
from drone_eval.view.tab_file_select import TabFileSelect
from drone_eval.view.tab_mission import TabMission
from drone_eval.view.tab_run import TabRun
from drone_eval.view.tab_summary import TabSummary
from drone_eval.view.tab_detail import TabDetail
from drone_eval.view.tab_visual import TabVisual
from drone_eval.view.tab_report import TabReport
from drone_eval.view.tab_preview import TabPreview
from drone_eval.view.tab_history import TabHistory
from drone_eval.view.tab_odm import TabODM


class MainWindow(QMainWindow):
    def __init__(self, controller: AppController) -> None:
        super().__init__()
        self._controller = controller
        self.setWindowTitle("드론 항공촬영 임무 평가 시스템")
        self.resize(1100, 700)

        self._tabs = QTabWidget()
        self.setCentralWidget(self._tabs)

        self._tab_file = TabFileSelect(controller)
        self._tab_mission = TabMission(controller)
        self._tab_run = TabRun(controller)
        self._tab_summary = TabSummary(controller)
        self._tab_detail = TabDetail(controller)
        self._tab_visual = TabVisual(controller)
        self._tab_report = TabReport(controller)
        self._tab_preview = TabPreview(controller)
        self._tab_history = TabHistory(controller)
        self._tab_odm = TabODM(controller)

        self._tabs.addTab(self._tab_file, "1. 파일 선택")
        self._tabs.addTab(self._tab_mission, "2. 임무 설정 확인")
        self._tabs.addTab(self._tab_run, "3. 평가 실행")
        self._tabs.addTab(self._tab_summary, "4. 결과 요약")
        self._tabs.addTab(self._tab_detail, "5. 상세 결과")
        self._tabs.addTab(self._tab_visual, "6. 시각화")
        self._tabs.addTab(self._tab_report, "7. 리포트 저장")
        self._tabs.addTab(self._tab_preview, "8. 입력 로그 확인")
        self._tabs.addTab(self._tab_history, "9. 평가 이력")
        self._tabs.addTab(self._tab_odm, "10. ODM 정사영상")

        self._status_bar = QStatusBar()
        self.setStatusBar(self._status_bar)
        self._status_bar.showMessage("파일을 선택하여 평가를 시작하세요.")

        self._tab_run.evaluation_finished.connect(self._on_evaluation_finished)
        self._tab_file.files_changed.connect(self._on_files_changed)

    def _on_files_changed(self) -> None:
        self._tab_mission.refresh()
        self._status_bar.showMessage("파일이 변경되었습니다.")

    def _on_evaluation_finished(self, success: bool, message: str) -> None:
        if success:
            self._tab_summary.refresh()
            self._tab_detail.refresh()
            self._tab_visual.refresh()
            self._tab_preview.refresh()
            self._tab_report.set_result_ready(True)
            self._tabs.setCurrentIndex(3)
            self._status_bar.showMessage("평가 완료.")
        else:
            self._status_bar.showMessage(f"평가 실패: {message}")
