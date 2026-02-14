"""
Author: Taylor
Project: Inspyre GPU Sheriff
File: admin.py

Description:
    Admin / elevation checks (required for PnP device toggles and scheduled task creation).
"""

from __future__ import annotations

import ctypes
import logging


def is_admin() -> bool:
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def ensure_admin_or_die(logger: logging.Logger) -> None:
    if is_admin():
        return

    logger.error('Administrator privileges are required for GPU device toggling.')
    logger.error('Run an elevated PowerShell OR install the scheduled task to run elevated at logon.')
    raise PermissionError('Admin privileges required.')
