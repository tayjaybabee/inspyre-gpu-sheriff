"""
Author: Taylor
Project: Inspyre GPU Sheriff
File: devcon.py

Description:
    Optional DevCon-based device bounce.
"""

from __future__ import annotations

from dataclasses import dataclass
import logging
import shutil
import subprocess
import time


@dataclass
class DevconGpuBouncer:
    instance_id: str
    logger: logging.Logger
    bounce_delay_s: float = 2.0
    devcon_path: str | None = None

    def _devcon(self) -> str:
        if self.devcon_path:
            return self.devcon_path
        found = shutil.which('devcon')
        if not found:
            raise FileNotFoundError('devcon.exe not found. Install DevCon or set devcon.path in config.')
        return found

    def run(self) -> None:
        devcon = self._devcon()
        self.logger.info(f'DevCon disable via {devcon}...')
        subprocess.run([devcon, 'disable', self.instance_id], check=True, capture_output=True, text=True)
        time.sleep(self.bounce_delay_s)
        self.logger.info('DevCon enable...')
        subprocess.run([devcon, 'enable', self.instance_id], check=True, capture_output=True, text=True)
