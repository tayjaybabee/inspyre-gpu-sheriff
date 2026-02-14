"""
Author: Taylor
Project: Inspyre GPU Sheriff
File: paths.py

Description:
    Centralized filesystem paths (config/logs).
"""

from __future__ import annotations

from pathlib import Path
import os


APP_DIR_NAME = 'InspyreGPU_Sheriff'


def app_dir() -> Path:
    base = os.environ.get('APPDATA')
    if not base:
        base = str(Path.home() / 'AppData' / 'Roaming')
    return Path(base) / APP_DIR_NAME
