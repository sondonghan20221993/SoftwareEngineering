from __future__ import annotations

import io
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D

from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFileDialog, QTextEdit, QGroupBox, QSplitter,
    QScrollArea,
)

from drone_eval.controller.app_controller import AppController
from drone_eval.service.odm_service import OdmService


class _OdmWorker(QThread):
    log = pyqtSignal(str)
    finished = pyqtSignal(bool)

    def __init__(self, project_dir: str) -> None:
        super().__init__()
        self._project_dir = project_dir

    def run(self) -> None:
        ok = OdmService.run_odm(self._project_dir, log_callback=self.log.emit)
        self.finished.emit(ok)


class TabODM(QWidget):
    def __init__(self, controller: AppController, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._controller = controller
        self._project_dir: str = ""
        self._worker: _OdmWorker | None = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        splitter = QSplitter(Qt.Vertical)

        # ── 상단: 설정 패널 ──────────────────────────────────────────
        config_group = QGroupBox("ODM 실행 설정")
        config_layout = QVBoxLayout()

        # 이미지 폴더
        img_row = QHBoxLayout()
        img_row.addWidget(QLabel("이미지 폴더:"))
        self._img_dir_edit = QLineEdit()
        self._img_dir_edit.setReadOnly(True)
        self._img_dir_edit.setPlaceholderText("촬영 이미지가 있는 폴더 선택...")
        img_row.addWidget(self._img_dir_edit)
        img_browse = QPushButton("찾아보기")
        img_browse.clicked.connect(self._browse_image_dir)
        img_row.addWidget(img_browse)
        config_layout.addLayout(img_row)

        # 출력 폴더
        out_row = QHBoxLayout()
        out_row.addWidget(QLabel("출력 폴더:"))
        self._out_dir_edit = QLineEdit()
        self._out_dir_edit.setReadOnly(True)
        self._out_dir_edit.setPlaceholderText("ODM 결과를 저장할 폴더 선택...")
        out_row.addWidget(self._out_dir_edit)
        out_browse = QPushButton("찾아보기")
        out_browse.clicked.connect(self._browse_out_dir)
        out_row.addWidget(out_browse)
        config_layout.addLayout(out_row)

        # 외부 이미지 폴더 (GPS EXIF 내장)
        ext_row = QHBoxLayout()
        ext_row.addWidget(QLabel("외부 이미지 폴더\n(GPS EXIF):"))
        self._ext_dir_edit = QLineEdit()
        self._ext_dir_edit.setReadOnly(True)
        self._ext_dir_edit.setPlaceholderText("GPS EXIF가 있는 이미지 폴더 (선택 사항)...")
        ext_row.addWidget(self._ext_dir_edit)
        ext_browse = QPushButton("찾아보기")
        ext_browse.clicked.connect(self._browse_ext_dir)
        ext_row.addWidget(ext_browse)
        config_layout.addLayout(ext_row)

        # 버튼 행
        btn_row = QHBoxLayout()
        self._prepare_btn = QPushButton("준비 (geo.txt 생성)")
        self._prepare_btn.clicked.connect(self._prepare)
        self._prepare_ext_btn = QPushButton("준비 (외부 이미지)")
        self._prepare_ext_btn.clicked.connect(self._prepare_from_folder)
        self._run_btn = QPushButton("▶ ODM 실행 (Docker)")
        self._run_btn.setEnabled(False)
        self._run_btn.clicked.connect(self._run_odm)
        self._load_btn = QPushButton("결과 불러오기")
        self._load_btn.clicked.connect(self._load_result)
        btn_row.addWidget(self._prepare_btn)
        btn_row.addWidget(self._prepare_ext_btn)
        btn_row.addWidget(self._run_btn)
        btn_row.addWidget(self._load_btn)
        btn_row.addStretch()
        config_layout.addLayout(btn_row)

        config_group.setLayout(config_layout)
        splitter.addWidget(config_group)

        # ── 중단: 로그 ───────────────────────────────────────────────
        log_group = QGroupBox("실행 로그")
        log_layout = QVBoxLayout()
        self._log_edit = QTextEdit()
        self._log_edit.setReadOnly(True)
        self._log_edit.setMaximumHeight(160)
        self._log_edit.setStyleSheet("font-family: monospace; font-size: 11px;")
        log_layout.addWidget(self._log_edit)
        log_group.setLayout(log_layout)
        splitter.addWidget(log_group)

        # ── 하단: 결과 뷰어 ─────────────────────────────────────────
        result_group = QGroupBox("정사영상 결과")
        result_layout = QVBoxLayout()
        self._result_label = QLabel("ODM 실행 후 결과가 여기에 표시됩니다.")
        self._result_label.setAlignment(Qt.AlignCenter)
        self._result_label.setStyleSheet("background: #1a1a2e;")
        scroll = QScrollArea()
        scroll.setWidget(self._result_label)
        scroll.setWidgetResizable(True)
        result_layout.addWidget(scroll)
        result_group.setLayout(result_layout)
        splitter.addWidget(result_group)

        splitter.setSizes([180, 160, 400])
        layout.addWidget(splitter)

    def _browse_image_dir(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "이미지 폴더 선택")
        if path:
            self._img_dir_edit.setText(path)

    def _browse_out_dir(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "출력 폴더 선택")
        if path:
            self._out_dir_edit.setText(path)

    def _browse_ext_dir(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "외부 이미지 폴더 선택")
        if path:
            self._ext_dir_edit.setText(path)

    def _log(self, msg: str) -> None:
        self._log_edit.append(msg)
        self._log_edit.verticalScrollBar().setValue(
            self._log_edit.verticalScrollBar().maximum()
        )

    def _prepare_from_folder(self) -> None:
        ext_dir = self._ext_dir_edit.text().strip()
        out_dir = self._out_dir_edit.text().strip()
        if not ext_dir:
            self._log("외부 이미지 폴더를 먼저 선택하세요.")
            return
        if not out_dir:
            self._log("출력 폴더를 먼저 선택하세요.")
            return
        try:
            project = OdmService.prepare_project_from_folder(ext_dir, out_dir)
            self._project_dir = str(project)
            count = len(list((project / "images").iterdir()))
            self._log(f"준비 완료: {project}")
            self._log(f"이미지 {count}장 복사 (GPS EXIF 모드)")
            self._run_btn.setEnabled(True)
        except Exception as exc:
            self._log(f"준비 실패: {exc}")

    def _prepare(self) -> None:
        out_dir = self._out_dir_edit.text().strip()
        if not out_dir:
            self._log("출력 폴더를 먼저 선택하세요.")
            return

        capture_records = self._controller.capture_records
        if not capture_records:
            self._log("평가를 먼저 실행하거나 촬영 로그를 로드하세요.")
            return

        try:
            project = OdmService.prepare_project(capture_records, out_dir)
            self._project_dir = str(project)
            img_count = len(list((project / "images").glob("*.png"))) + \
                        len(list((project / "images").glob("*.jpg")))
            self._log(f"준비 완료: {project}")
            self._log(f"이미지 {img_count}장 복사, geo.txt 생성")
            self._run_btn.setEnabled(True)
        except Exception as exc:
            self._log(f"준비 실패: {exc}")

    def _run_odm(self) -> None:
        if not self._project_dir:
            self._log("먼저 '준비' 버튼을 눌러주세요.")
            return

        self._run_btn.setEnabled(False)
        self._log("ODM 실행 시작...")
        self._worker = _OdmWorker(self._project_dir)
        self._worker.log.connect(self._log)
        self._worker.finished.connect(self._on_odm_finished)
        self._worker.start()

    def _on_odm_finished(self, success: bool) -> None:
        self._run_btn.setEnabled(True)
        if success:
            self._log("ODM 완료! '결과 불러오기'를 눌러주세요.")
        else:
            self._log("ODM 실패. 로그를 확인하세요.")

    def _load_result(self) -> None:
        project_dir = self._project_dir or self._out_dir_edit.text().strip()
        if not project_dir:
            path, _ = QFileDialog.getOpenFileName(
                self, "정사영상 파일 선택", "",
                "이미지 (*.tif *.tiff *.png);;모든 파일 (*)"
            )
            if not path:
                return
            ortho_path = Path(path)
        else:
            ortho_path = OdmService.find_orthophoto(project_dir)
            if ortho_path is None:
                self._log(f"정사영상을 찾을 수 없습니다: {project_dir}/odm_orthophoto/")
                return

        self._log(f"불러오는 중: {ortho_path}")
        try:
            capture_records = self._controller.capture_records
            img, x_min, x_max, y_min, y_max = OdmService.load_orthophoto(
                ortho_path, capture_records
            )
            self._show_overlay(img, x_min, x_max, y_min, y_max)
            self._log("정사영상 로드 완료.")
        except Exception as exc:
            self._log(f"로드 실패: {exc}")

    def _show_overlay(
        self,
        img: np.ndarray,
        x_min: float, x_max: float,
        y_min: float, y_max: float,
    ) -> None:
        result = self._controller.eval_result
        mission = self._controller.mission

        fig, ax = plt.subplots(figsize=(9, 9))
        ax.imshow(img, extent=[x_min, x_max, y_min, y_max],
                  origin="upper", aspect="equal")

        if mission is not None:
            for tgt in mission.targets:
                ax.scatter(tgt.x, tgt.y, marker="x", s=160,
                           c="red", linewidths=2.5, zorder=5)
                ax.annotate(tgt.target_id, (tgt.x, tgt.y),
                            textcoords="offset points", xytext=(6, 6),
                            fontsize=9, color="red", fontweight="bold")

        if result is not None:
            for tr in result.target_results:
                if tr.is_missing or tr.matched_capture is None:
                    continue
                cap = tr.matched_capture
                color = "lime" if (tr.position_ok and tr.direction_ok and tr.time_ok) else "orange"
                ax.scatter(cap.x, cap.y, marker="o", s=80,
                           c=color, zorder=4, edgecolors="white", linewidths=0.5)

        legend_elements = [
            Line2D([0], [0], marker="x", color="red", label="Target",
                   markersize=9, linestyle="None", markeredgewidth=2),
            Line2D([0], [0], marker="o", color="lime", label="Capture OK",
                   markersize=8, linestyle="None"),
            Line2D([0], [0], marker="o", color="orange", label="Capture Failed",
                   markersize=8, linestyle="None"),
        ]
        ax.legend(handles=legend_elements, loc="upper left",
                  bbox_to_anchor=(1.01, 1), borderaxespad=0, fontsize=8)
        ax.set_title("ODM Orthophoto + Mission Overlay")
        ax.set_xlabel("X (m)")
        ax.set_ylabel("Y (m)")
        ax.grid(True, alpha=0.2, color="white")
        fig.tight_layout()

        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=120, bbox_inches="tight")
        plt.close(fig)
        buf.seek(0)
        qimg = QImage.fromData(buf.read())
        pixmap = QPixmap.fromImage(qimg)
        self._result_label.setPixmap(pixmap)
        self._result_label.resize(pixmap.size())
