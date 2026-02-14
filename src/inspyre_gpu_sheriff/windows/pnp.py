"""
Author: Taylor
Project: Inspyre GPU Sheriff
File: pnp.py

Description:
    PnP device discovery and bounce operations via PowerShell PnpDevice cmdlets.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import logging
import time

from .powershell import run_powershell


def _json_to_list(out: str) -> list[dict]:
    data = json.loads(out)
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return [data]
    return []


@dataclass
class PnpGpuResolver:
    prefer_vendor: str
    prefer_name_contains: str
    logger: logging.Logger

    def list_display_devices(self) -> list[dict]:
        ps = r"""
        $ErrorActionPreference = 'Stop'
        $devs = Get-PnpDevice -Class Display | Select-Object FriendlyName, InstanceId, Status, ProblemCode
        $devs | ConvertTo-Json -Depth 4
        """
        out = run_powershell(ps, check=True)
        if not out:
            return []
        return _json_to_list(out)

    def pick_best_gpu_instance_id(self) -> str | None:
        devs = self.list_display_devices()
        if not devs:
            return None

        scored: list[tuple[int, dict]] = []
        for d in devs:
            name = (d.get('FriendlyName') or '').upper()
            iid = (d.get('InstanceId') or '').upper()
            score = 0

            if self.prefer_vendor.upper() in iid:
                score += 50
            if self.prefer_name_contains and self.prefer_name_contains.upper() in name:
                score += 40
            if 'MICROSOFT BASIC DISPLAY' in name:
                score -= 100
            if 'RADEON' in name or 'AMD' in name:
                score += 10

            scored.append((score, d))

        scored.sort(key=lambda t: t[0], reverse=True)
        best = scored[0][1]
        best_id = best.get('InstanceId')
        if best_id:
            self.logger.info(f"Auto-selected target: {best.get('FriendlyName')} | {best_id}")
        return best_id


@dataclass
class PnpGpuBouncer:
    instance_id: str
    logger: logging.Logger
    bounce_delay_s: float = 2.0

    def run(self) -> None:
        disable = f"Disable-PnpDevice -InstanceId '{self.instance_id}' -Confirm:$false -ErrorAction Stop"
        enable = f"Enable-PnpDevice -InstanceId '{self.instance_id}' -Confirm:$false -ErrorAction Stop"

        self.logger.info('PnP disable...')
        run_powershell(disable, check=True)
        time.sleep(self.bounce_delay_s)
        self.logger.info('PnP enable...')
        run_powershell(enable, check=True)
