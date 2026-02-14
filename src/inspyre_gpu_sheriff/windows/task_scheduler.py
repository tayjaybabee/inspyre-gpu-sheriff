"""
Author: Taylor
Project: Inspyre GPU Sheriff
File: task_scheduler.py

Description:
    Create/remove a Scheduled Task to run 'inspy-gpu watch' at logon with highest privileges.
"""

from __future__ import annotations

from dataclasses import dataclass
import logging
import subprocess
import sys


@dataclass
class TaskSchedulerManager:
    logger: logging.Logger

    def install_task(self, task_name: str, python_exe: str | None = None) -> None:
        python_exe = python_exe or sys.executable
        cmd = f'"{python_exe}" -m inspyre_gpu_sheriff.cli watch'

        schtasks = [
            'schtasks',
            '/Create',
            '/F',
            '/RL',
            'HIGHEST',
            '/SC',
            'ONLOGON',
            '/TN',
            task_name,
            '/TR',
            cmd,
        ]

        self.logger.info(f'Creating scheduled task: {task_name}')
        subprocess.run(schtasks, check=True, capture_output=True, text=True)
        self.logger.info('Scheduled task installed.')

    def uninstall_task(self, task_name: str) -> None:
        self.logger.info(f'Deleting scheduled task: {task_name}')
        subprocess.run(['schtasks', '/Delete', '/TN', task_name, '/F'], check=True, capture_output=True, text=True)
        self.logger.info('Scheduled task removed.')
