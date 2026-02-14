"""
Author: Taylor
Project: Inspyre GPU Sheriff
File: snapshot.py

Description:
    Collect incident snapshots for debugging:
    - dxdiag adapters
    - PnP display devices
    - recent System log events (as already detected)
    - running processes (top N by CPU time)

Dependencies:
    - psutil
"""

from __future__ import annotations

from dataclasses import dataclass
import logging
import psutil

from .dxdiag import DxDiag
from .pnp import PnpGpuResolver


@dataclass
class IncidentSnapshotter:
    logger: logging.Logger
    prefer_vendor: str
    prefer_name_contains: str
    process_limit: int = 50

    def collect(self, *, eventlog_incident: dict | None = None) -> dict:
        dx = DxDiag(self.logger)
        resolver = PnpGpuResolver(
            prefer_vendor=self.prefer_vendor,
            prefer_name_contains=self.prefer_name_contains,
            logger=self.logger,
        )

        procs = self._top_processes(limit=self.process_limit)

        snap = {
            'dxdiag_adapters': dx.list_display_adapters(),
            'pnp_display_devices': resolver.list_display_devices(),
            'processes_top': procs,
            'eventlog_incident': eventlog_incident,
        }
        return snap

    def _top_processes(self, limit: int) -> list[dict]:
        items = []
        for p in psutil.process_iter(['pid', 'name', 'cpu_times', 'create_time']):
            try:
                ct = p.info.get('cpu_times')
                cpu_total = float(ct.user + ct.system) if ct else 0.0
                items.append({'pid': p.info['pid'], 'name': p.info.get('name'), 'cpu_total_s': cpu_total})
            except Exception:
                continue

        items.sort(key=lambda d: d.get('cpu_total_s', 0.0), reverse=True)
        return items[: max(1, limit)]
