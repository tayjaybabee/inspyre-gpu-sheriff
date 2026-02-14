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

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box

from .config import load_config, save_config, config_path
from .logging_ import setup_logging
from .platform_ import is_windows
from .core.doctor import GPUSheriff


def _pretty(obj: object) -> str:
    return json.dumps(obj, indent=2, ensure_ascii=False)


def _get_device_friendly_name(devices: list[dict], instance_id: str) -> str:
    """Get the friendly name for a device given its instance ID."""
    for device in devices:
        if device.get('InstanceId') == instance_id:
            return device.get('FriendlyName', 'Unknown')
    return 'Unknown'


def _format_status_rich(info: dict) -> None:
    """Format and display status information using rich library."""
    console = Console()
    
    # Display PnP Display Devices
    devices = info.get('pnp_display_devices', [])
    if devices:
        table = Table(title="PnP Display Devices", box=box.ROUNDED, show_header=True, header_style="bold magenta")
        table.add_column("Friendly Name", style="cyan", no_wrap=False)
        table.add_column("Instance ID", style="yellow", no_wrap=False)
        table.add_column("Status", style="green")
        table.add_column("Problem Code", style="red")
        
        for device in devices:
            friendly_name = device.get('FriendlyName', 'N/A')
            instance_id = device.get('InstanceId', 'N/A')
            status = device.get('Status', 'N/A')
            problem_code = str(device.get('ProblemCode', 'None'))
            
            # Color code the status
            if status == 'OK':
                status_text = Text(status, style="bold green")
            else:
                status_text = Text(status, style="bold red")
            
            table.add_row(friendly_name, instance_id, status_text, problem_code)
        
        console.print(table)
    
    # Display Auto-selected Target
    auto_target = info.get('auto_target_instance_id', '')
    if auto_target:
        target_name = _get_device_friendly_name(devices, auto_target)
        
        panel = Panel(
            f"[bold cyan]{target_name}[/bold cyan]\n[yellow]{auto_target}[/yellow]",
            title="[bold green]Auto-Selected Target GPU[/bold green]",
            border_style="green",
            box=box.DOUBLE
        )
        console.print(panel)
    
    # Display Config Target if set
    config_target = info.get('config_target_instance_id', '')
    if config_target:
        target_name = _get_device_friendly_name(devices, config_target)
        
        panel = Panel(
            f"[bold cyan]{target_name}[/bold cyan]\n[yellow]{config_target}[/yellow]",
            title="[bold blue]Configured Target GPU[/bold blue]",
            border_style="blue",
            box=box.DOUBLE
        )
        console.print(panel)
    else:
        console.print(Panel(
            "[dim]No specific target configured - using auto-selection[/dim]",
            title="[bold blue]Configured Target GPU[/bold blue]",
            border_style="blue",
            box=box.ROUNDED
        ))


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
            _format_status_rich(info)
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
