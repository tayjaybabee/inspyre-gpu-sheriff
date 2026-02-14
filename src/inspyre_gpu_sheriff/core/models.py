"""
Author: Taylor
Project: Inspyre GPU Sheriff
File: models.py

Description:
    Core configuration models.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class RecoveryStep(str, Enum):
    HOTKEY_RESET = 'hotkey_reset'
    PNP_BOUNCE = 'pnp_bounce'
    DEVCON_BOUNCE = 'devcon_bounce'


@dataclass(frozen=True)
class SheriffConfig:
    device_instance_id: str | None
    prefer_vendor: str
    prefer_name_contains: str
    escalation: tuple[RecoveryStep, ...]
    bounce_delay_s: float
    watch_interval_s: float
    eventlog_enabled: bool
    eventlog_lookback_s: int
    auto_recover: bool
    devcon_path: str | None
    task_name: str
    python_exe_hint: str | None

    # Safety rails
    cooldown_s: int
    max_attempts_per_10m: int

    # Snapshot tuning
    snapshot_process_limit: int
