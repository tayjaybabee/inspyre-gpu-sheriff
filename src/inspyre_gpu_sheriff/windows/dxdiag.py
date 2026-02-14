"""
Author: Taylor
Project: Inspyre GPU Sheriff
File: dxdiag.py

Description:
    Uses dxdiag to snapshot adapter names (handy for status + incident snapshots).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import logging
import subprocess
import tempfile


@dataclass
class DxDiag:
    logger: logging.Logger

    def list_display_adapters(self) -> list[str]:
        with tempfile.TemporaryDirectory() as td:
            out_path = Path(td) / 'dxdiag.txt'
            subprocess.run(
                ['dxdiag', '/t', str(out_path)],
                check=True,
                capture_output=True,
                text=True
            )

        # Try multiple encodings defensively
        raw = out_path.read_bytes()

        text = None
        for enc in ('utf-16', 'utf-16le', 'utf-8', 'cp1252'):
            try:
                text = raw.decode(enc)
                break
            except Exception:
                continue

        if text is None:
            raise RuntimeError('Failed to decode dxdiag output.')

        adapters: list[str] = []
        for line in text.splitlines():
            if line.strip().lower().startswith('card name:'):
                adapters.append(line.split(':', 1)[1].strip())

        return adapters
