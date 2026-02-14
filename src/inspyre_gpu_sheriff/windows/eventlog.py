"""
Author: Taylor
Project: Inspyre GPU Sheriff
File: eventlog.py

Description:
    Heuristic incident detection from System event log.

Notes:
    - We look for ProviderName matches and classic 4101 TDR-style events.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import logging

from .powershell import run_powershell


def _json_to_list(out: str) -> list[dict]:
    try:
        data = json.loads(out)
    except Exception:
        return []
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return [data]
    return []


@dataclass
class WindowsEventLogDetector:
    logger: logging.Logger
    enabled: bool = True
    lookback_s: int = 25

    def is_incident(self) -> dict | None:
        if not self.enabled:
            return None

        ps = rf"""
        $ErrorActionPreference = 'SilentlyContinue'
        $start = (Get-Date).AddSeconds(-{int(self.lookback_s)})
        $events = Get-WinEvent -FilterHashtable @{{LogName='System'; StartTime=$start}} |
            Where-Object {{
                $_.ProviderName -match 'Display|amdkmdag|amdwddmg|nvlddmkm|igfx' -or
                $_.Message -match 'stopped responding|recovered|TDR|Timeout Detection' -or
                $_.Id -in 4101
            }} |
            Select-Object TimeCreated, Id, ProviderName, LevelDisplayName, Message |
            Sort-Object TimeCreated -Descending |
            Select-Object -First 5

        if (-not $events) {{ return '' }}
        $events | ConvertTo-Json -Depth 4
        """

        out = run_powershell(ps, check=False)
        if not out:
            return None

        events = _json_to_list(out)
        if not events:
            return None

        return {'events': events, 'lookback_s': self.lookback_s}
