"""
Author: Taylor
Project: Inspyre GPU Sheriff
File: powershell.py

Description:
    Safe-ish PowerShell runner wrapper.
"""

from __future__ import annotations

import subprocess


def run_powershell(ps: str, *, check: bool = True) -> str:
    result = subprocess.run(
        ['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command', ps],
        check=check,
        capture_output=True,
        text=True,
    )
    return (result.stdout or '').strip()
