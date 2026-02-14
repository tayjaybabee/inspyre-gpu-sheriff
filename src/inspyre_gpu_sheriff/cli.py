"""
Author: Taylor
Project: Inspyre GPU Sheriff
File: cli.py

Description:
    CLI entry point for the Sheriff.

Commands:
    - status
    - watch
    - reset
    - install-task
    - uninstall-task
    - set-device
    - print-config
"""

from __future__ import annotations

import argparse
import json
import logging

from .config import load_config, save_config, config_path
from .logging_ import setup_logging
from .platform_ import is_windows
from .core.doctor import GPUSheriff


def _pretty(obj: object) -> str:
    return json.dumps(obj, indent=2, ensure_ascii=False)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog='inspy-gpu', description='Inspyre GPU Sheriff (Windows)')
    p.add_argument('--debug', action='store_true', help='Verbose logging.')

    sub = p.add_subparsers(dest='cmd', required=True)

    sub.add_parser('status', help='Show detected adapters and PnP display devices.')
    sub.add_parser('watch', help='Watch for incidents and auto-recover (foreground).')
    sub.add_parser('reset', help='Run the recovery ladder once (manual).')

    it = sub.add_parser('install-task', help='Install Task Scheduler job to run watch at logon (elevated).')
    it.add_argument('--task-name', default=None, help='Override configured task name.')
    it.add_argument('--python', dest='python_exe', default=None, help='Override python executable.')

    ut = sub.add_parser('uninstall-task', help='Remove Task Scheduler job.')
    ut.add_argument('--task-name', default=None, help='Override configured task name.')

    sd = sub.add_parser('set-device', help='Set fixed target GPU PnP InstanceId in config.')
    sd.add_argument('instance_id', help='PnP InstanceId for the dGPU.')

    sub.add_parser('print-config', help='Print config path and contents.')

    return p


def main() -> None:
    args = build_parser().parse_args()
    level = logging.DEBUG if args.debug else logging.INFO
    logger = setup_logging(level=level)

    if not is_windows():
        raise SystemExit('Windows only (at the moment).')

    cfg = load_config()
    sheriff = GPUSheriff(config=cfg, logger=logger)

    match args.cmd:
        case 'status':
            info = sheriff.status()
            print(_pretty(info))
        case 'watch':
            sheriff.watch_forever()
        case 'reset':
            sheriff.reset_now()
        case 'install-task':
            sheriff.install_task(task_name=args.task_name, python_exe=args.python_exe)
        case 'uninstall-task':
            sheriff.uninstall_task(task_name=args.task_name)
        case 'set-device':
            cfg2 = cfg.__class__(**{**cfg.__dict__, 'device_instance_id': args.instance_id})
            save_config(cfg2)
            print('Saved device.instance_id to config.')
        case 'print-config':
            p = config_path()
            print(str(p))
            print(p.read_text(encoding='utf-8'))
        case _:
            raise SystemExit(f'Unknown command: {args.cmd}')
