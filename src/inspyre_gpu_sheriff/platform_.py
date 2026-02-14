"""
Author: Taylor
Project: Inspyre GPU Sheriff
File: platform_.py

Description:
    Platform detection helpers.
"""

import os
import sys


def is_windows() -> bool:
    return os.name == 'nt' and sys.platform.startswith('win')
