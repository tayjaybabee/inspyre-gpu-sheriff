"""
Author: Taylor
Project: Inspyre GPU Sheriff
File: hotkey.py

Description:
    Sends Win+Ctrl+Shift+B to reset the Windows graphics stack.
"""

from __future__ import annotations

from dataclasses import dataclass
import ctypes
import logging
import time

VK_LWIN = 0x5B
VK_CONTROL = 0x11
VK_SHIFT = 0x10
VK_B = 0x42

KEYEVENTF_KEYUP = 0x0002


def _keybd_event(vk: int, flags: int = 0) -> None:
    ctypes.windll.user32.keybd_event(vk, 0, flags, 0)


@dataclass
class GraphicsHotkeyReset:
    logger: logging.Logger

    def run(self) -> None:
        self.logger.info('Sending graphics reset hotkey: Win+Ctrl+Shift+B')
        _keybd_event(VK_LWIN)
        _keybd_event(VK_CONTROL)
        _keybd_event(VK_SHIFT)
        time.sleep(0.05)

        _keybd_event(VK_B)
        time.sleep(0.05)
        _keybd_event(VK_B, KEYEVENTF_KEYUP)

        time.sleep(0.05)
        _keybd_event(VK_SHIFT, KEYEVENTF_KEYUP)
        _keybd_event(VK_CONTROL, KEYEVENTF_KEYUP)
        _keybd_event(VK_LWIN, KEYEVENTF_KEYUP)

        time.sleep(1.0)
