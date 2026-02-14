"""
Author: Taylor
Project: Inspyre GPU Sheriff
File: config.py

Description:
    Load/save TOML configuration.

Dependencies:
    - Python 3.11+ (tomllib)
"""

from __future__ import annotations

from pathlib import Path
import tomllib

from .paths import app_dir
from .core.models import RecoveryStep, SheriffConfig


CONFIG_NAME = 'config.toml'


def config_path() -> Path:
    return app_dir() / CONFIG_NAME


def default_config() -> SheriffConfig:
    return SheriffConfig(
        device_instance_id=None,
        prefer_vendor='VEN_1002',
        prefer_name_contains='7700S',
        escalation=(
            RecoveryStep.HOTKEY_RESET,
            RecoveryStep.PNP_BOUNCE,
            RecoveryStep.DEVCON_BOUNCE,
        ),
        bounce_delay_s=2.0,
        watch_interval_s=2.0,
        eventlog_enabled=True,
        eventlog_lookback_s=25,
        auto_recover=True,
        devcon_path=None,
        task_name='Inspyre GPU Sheriff',
        python_exe_hint=None,
        # safety rails
        cooldown_s=60,
        max_attempts_per_10m=3,
        snapshot_process_limit=50,
    )


def load_config() -> SheriffConfig:
    app_dir().mkdir(parents=True, exist_ok=True)
    p = config_path()
    if not p.exists():
        cfg = default_config()
        save_config(cfg)
        return cfg

    raw = tomllib.loads(p.read_text(encoding='utf-8'))

    # Recovery steps
    steps_raw = raw.get('recovery', {}).get('escalation', None)
    escalation = tuple(RecoveryStep(s) for s in steps_raw) if steps_raw else default_config().escalation

    cfg = default_config()
    device_instance_id = raw.get('device', {}).get('instance_id', cfg.device_instance_id)
    prefer_vendor = raw.get('device', {}).get('prefer_vendor', cfg.prefer_vendor)
    prefer_name_contains = raw.get('device', {}).get('prefer_name_contains', cfg.prefer_name_contains)

    bounce_delay_s = float(raw.get('recovery', {}).get('bounce_delay_s', cfg.bounce_delay_s))

    watch_interval_s = float(raw.get('watch', {}).get('interval_s', cfg.watch_interval_s))
    eventlog_enabled = bool(raw.get('watch', {}).get('eventlog_enabled', cfg.eventlog_enabled))
    eventlog_lookback_s = int(raw.get('watch', {}).get('eventlog_lookback_s', cfg.eventlog_lookback_s))
    auto_recover = bool(raw.get('watch', {}).get('auto_recover', cfg.auto_recover))

    cooldown_s = int(raw.get('safety', {}).get('cooldown_s', cfg.cooldown_s))
    max_attempts_per_10m = int(raw.get('safety', {}).get('max_attempts_per_10m', cfg.max_attempts_per_10m))
    snapshot_process_limit = int(raw.get('snapshot', {}).get('process_limit', cfg.snapshot_process_limit))

    devcon_path = raw.get('devcon', {}).get('path', cfg.devcon_path)
    task_name = raw.get('task', {}).get('name', cfg.task_name)
    python_exe_hint = raw.get('task', {}).get('python_exe_hint', cfg.python_exe_hint)

    return SheriffConfig(
        device_instance_id=device_instance_id,
        prefer_vendor=prefer_vendor,
        prefer_name_contains=prefer_name_contains,
        escalation=escalation,
        bounce_delay_s=bounce_delay_s,
        watch_interval_s=watch_interval_s,
        eventlog_enabled=eventlog_enabled,
        eventlog_lookback_s=eventlog_lookback_s,
        auto_recover=auto_recover,
        devcon_path=devcon_path,
        task_name=task_name,
        python_exe_hint=python_exe_hint,
        cooldown_s=cooldown_s,
        max_attempts_per_10m=max_attempts_per_10m,
        snapshot_process_limit=snapshot_process_limit,
    )


def save_config(cfg: SheriffConfig) -> None:
    app_dir().mkdir(parents=True, exist_ok=True)
    p = config_path()
    p.write_text(_to_toml(cfg), encoding='utf-8')


def _to_toml(cfg: SheriffConfig) -> str:
    esc = ', '.join([f"'{s.value}'" for s in cfg.escalation])

    if cfg.device_instance_id:
        device_id_line = f"instance_id = '{cfg.device_instance_id}'"
    else:
        device_id_line = "instance_id = ''"

    if cfg.devcon_path:
        devcon_path_line = f"path = '{cfg.devcon_path}'"
    else:
        devcon_path_line = "path = ''"

    if cfg.python_exe_hint:
        python_hint_line = f"python_exe_hint = '{cfg.python_exe_hint}'"
    else:
        python_hint_line = "python_exe_hint = ''"

    return f"""# Inspyre GPU Sheriff config

[device]
{device_id_line}
prefer_vendor = '{cfg.prefer_vendor}'
prefer_name_contains = '{cfg.prefer_name_contains}'

[recovery]
escalation = [{esc}]
bounce_delay_s = {cfg.bounce_delay_s}

[watch]
interval_s = {cfg.watch_interval_s}
eventlog_enabled = {str(cfg.eventlog_enabled).lower()}
eventlog_lookback_s = {cfg.eventlog_lookback_s}
auto_recover = {str(cfg.auto_recover).lower()}

[safety]
cooldown_s = {cfg.cooldown_s}
max_attempts_per_10m = {cfg.max_attempts_per_10m}

[snapshot]
process_limit = {cfg.snapshot_process_limit}

[devcon]
{devcon_path_line}

[task]
name = '{cfg.task_name}'
{python_hint_line}
"""
