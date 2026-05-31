from __future__ import annotations

import logging
import sys
from pathlib import Path


_APP_LOGGER_NAME = "drone_eval"


def get_logger(name: str = _APP_LOGGER_NAME) -> logging.Logger:
    return logging.getLogger(name)


def setup_logging(log_dir: str | Path | None = None, level: int = logging.DEBUG) -> None:
    root = logging.getLogger(_APP_LOGGER_NAME)
    if root.handlers:
        return

    root.setLevel(level)

    fmt = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.WARNING)
    console_handler.setFormatter(fmt)
    root.addHandler(console_handler)

    if log_dir is not None:
        log_path = Path(log_dir) / "drone_eval.log"
        try:
            log_path.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_path, encoding="utf-8")
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(fmt)
            root.addHandler(file_handler)
        except OSError as exc:
            root.warning("Could not create log file at '%s': %s", log_path, exc)
