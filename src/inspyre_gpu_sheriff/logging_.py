"""
Author: Taylor
Project: Inspyre GPU Sheriff
File: logging_.py

Description:
    Logger + JSONL incident logging.

Dependencies:
    - Python 3.11+
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
import logging
import os
import time

from .paths import app_dir


@dataclass(frozen=True)
class LogPaths:
    folder: Path
    text_log: Path
    jsonl_log: Path


def log_paths() -> LogPaths:
    folder = app_dir()
    folder.mkdir(parents=True, exist_ok=True)
    return LogPaths(
        folder=folder,
        text_log=folder / 'inspyre_gpu_sheriff.log',
        jsonl_log=folder / 'inspyre_gpu_sheriff.jsonl',
    )


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    paths = log_paths()
    logger = logging.getLogger('inspyre_gpu_sheriff')
    logger.setLevel(level)
    logger.propagate = False

    if logger.handlers:
        return logger

    fmt = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')

    fh = logging.FileHandler(paths.text_log, encoding='utf-8')
    fh.setLevel(level)
    fh.setFormatter(fmt)

    sh = logging.StreamHandler()
    sh.setLevel(level)
    sh.setFormatter(fmt)

    logger.addHandler(fh)
    logger.addHandler(sh)
    return logger


def log_json(event: dict) -> None:
    paths = log_paths()
    payload = dict(event)
    payload['ts_unix'] = time.time()

    with paths.jsonl_log.open('a', encoding='utf-8') as f:
        f.write(json.dumps(payload, ensure_ascii=False) + '\n')
