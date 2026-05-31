from __future__ import annotations

import sys
from pathlib import Path

from PyQt5.QtWidgets import QApplication

from drone_eval.controller.app_controller import AppController
from drone_eval.utils.logger import setup_logging
from drone_eval.view.main_window import MainWindow


def main() -> None:
    log_dir = Path.home() / ".drone_eval" / "logs"
    setup_logging(log_dir=log_dir)

    history_dir = Path.home() / ".drone_eval" / "history"

    app = QApplication(sys.argv)
    app.setApplicationName("드론 항공촬영 임무 평가 시스템")

    controller = AppController(history_dir=history_dir)
    window = MainWindow(controller)
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
