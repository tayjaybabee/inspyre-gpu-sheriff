"""
Author: Taylor
Project: Inspyre GPU Sheriff
File: doctor.py

Description:
    Orchestration: status, watch loop, incident detection, snapshots, and recovery escalation.

Safety:
    - Rate limit attempts (max_attempts_per_10m)
    - Cooldown after successful recovery (cooldown_s)
"""

from __future__ import annotations

from dataclasses import dataclass
import logging
import time

from .models import RecoveryStep, SheriffConfig
from .ratelimit import RecoveryLimiter
from ..logging_ import log_json
from ..platform_ import is_windows
from ..windows.admin import ensure_admin_or_die
from ..windows.eventlog import WindowsEventLogDetector
from ..windows.hotkey import GraphicsHotkeyReset
from ..windows.pnp import PnpGpuBouncer, PnpGpuResolver
from ..windows.devcon import DevconGpuBouncer
from ..windows.snapshot import IncidentSnapshotter
from ..windows.task_scheduler import TaskSchedulerManager



@dataclass
class GPUSheriff:
    config: SheriffConfig
    logger: logging.Logger

    def _resolver(self) -> PnpGpuResolver:
        return PnpGpuResolver(
            prefer_vendor=self.config.prefer_vendor,
            prefer_name_contains=self.config.prefer_name_contains,
            logger=self.logger,
        )

    def _resolve_target(self) -> str:
        if self.config.device_instance_id:
            return self.config.device_instance_id

        target = self._resolver().pick_best_gpu_instance_id()
        if not target:
            raise RuntimeError('Could not auto-resolve a target dGPU InstanceId.')
        return target

    def status(self) -> dict:
        if not is_windows():
            raise RuntimeError('Windows only.')

        resolver = self._resolver()

        return {
            'pnp_display_devices': resolver.list_display_devices(),
            'auto_target_instance_id': resolver.pick_best_gpu_instance_id(),
            'config_target_instance_id': self.config.device_instance_id,
        }

    def reset_now(self) -> None:
        ensure_admin_or_die(self.logger)
        target = self._resolve_target()
        self._recover(target, reason='manual_reset', incident=None)

    def watch_forever(self) -> None:
        ensure_admin_or_die(self.logger)
        target = self._resolve_target()

        detector = WindowsEventLogDetector(
            logger=self.logger,
            enabled=self.config.eventlog_enabled,
            lookback_s=self.config.eventlog_lookback_s,
        )

        limiter = RecoveryLimiter(
            cooldown_s=self.config.cooldown_s,
            max_attempts_per_10m=self.config.max_attempts_per_10m,
        )

        snapshotter = IncidentSnapshotter(
            logger=self.logger,
            prefer_vendor=self.config.prefer_vendor,
            prefer_name_contains=self.config.prefer_name_contains,
            process_limit=self.config.snapshot_process_limit,
        )

        self.logger.info(f'Watching for incidents. Target: {target}')
        log_json({'event': 'watch_start', 'target': target})

        while True:
            incident = detector.is_incident()
            if incident:
                self.logger.warning('Incident detected (event log heuristic).')
                snap = snapshotter.collect(eventlog_incident=incident)

                log_json({'event': 'incident', 'target': target, 'incident': incident, 'snapshot': snap})

                if not self.config.auto_recover:
                    self.logger.warning('auto_recover disabled; not attempting recovery.')
                else:
                    ok, why = limiter.can_attempt()
                    if not ok:
                        self.logger.warning(f'Recovery blocked: {why}')
                        log_json({'event': 'recovery_blocked', 'target': target, 'reason': why})
                    else:
                        limiter.note_attempt()
                        try:
                            self._recover(target, reason='watch_incident', incident={'incident': incident, 'snapshot': snap})
                            limiter.note_success()
                        except Exception as e:
                            self.logger.error(f'Recovery failed: {type(e).__name__}: {e}')
            time.sleep(self.config.watch_interval_s)

    def _recover(self, target_instance_id: str, reason: str, incident: dict | None) -> None:
        recoveries = {
            RecoveryStep.HOTKEY_RESET: GraphicsHotkeyReset(self.logger),
            RecoveryStep.PNP_BOUNCE: PnpGpuBouncer(
                instance_id=target_instance_id,
                logger=self.logger,
                bounce_delay_s=self.config.bounce_delay_s,
            ),
            RecoveryStep.DEVCON_BOUNCE: DevconGpuBouncer(
                instance_id=target_instance_id,
                logger=self.logger,
                bounce_delay_s=self.config.bounce_delay_s,
                devcon_path=self.config.devcon_path,
            ),
        }

        self.logger.info(f'Recovery started. reason={reason} escalation={[s.value for s in self.config.escalation]}')
        log_json(
            {
                'event': 'recovery_start',
                'reason': reason,
                'incident': incident,
                'target': target_instance_id,
                'escalation': [s.value for s in self.config.escalation],
            }
        )

        last_error: str | None = None

        for step in self.config.escalation:
            rec = recoveries.get(step)
            if not rec:
                continue

            try:
                self.logger.info(f'Attempting step: {step.value}')
                rec.run()
                self.logger.info(f'Step succeeded: {step.value}')
                log_json({'event': 'recovery_step_ok', 'step': step.value, 'target': target_instance_id})
                return
            except Exception as e:
                last_error = f'{type(e).__name__}: {e}'
                self.logger.error(f'Step failed: {step.value} | {last_error}')
                log_json({'event': 'recovery_step_fail', 'step': step.value, 'error': last_error, 'target': target_instance_id})

        msg = f'All recovery steps failed. last_error={last_error}'
        self.logger.error(msg)
        log_json({'event': 'recovery_failed', 'target': target_instance_id, 'last_error': last_error})
        raise RuntimeError(msg)

    def install_task(self, task_name: str | None = None, python_exe: str | None = None) -> None:
        ensure_admin_or_die(self.logger)
        mgr = TaskSchedulerManager(self.logger)
        mgr.install_task(task_name or self.config.task_name, python_exe or self.config.python_exe_hint)

    def uninstall_task(self, task_name: str | None = None) -> None:
        ensure_admin_or_die(self.logger)
        mgr = TaskSchedulerManager(self.logger)
        mgr.uninstall_task(task_name or self.config.task_name)
