#!/usr/bin/env python

import ctypes
import platform

if platform.system() == 'Windows':
    kernel32 = ctypes.windll.kernel32
    kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)

COMMANDS = {
    'green': 32,
    'lightgreen': 92,
    'grey': 37,
    'black': 30,
    'red': 31,
    'lightred': 91,
    'cyan': 36,
    'lightcyan': 96,
    'blue': 34,
    'lightblue': 94,
    'purple': 35,
    'yellow': 93,
    'white': 97,
    'lightpurple': 95,
    'orange': 33
}


def _gen(string, prefix, key):
    colored = prefix if prefix else string
    not_colored = string if prefix else ''
    return u'\033[{}m{}\033[0m{}\n'.format(key, colored, not_colored)


for key, val in COMMANDS.items():
    value = val[0] if isinstance(val, tuple) else val
    prefix = val[1] if isinstance(val, tuple) else ''
    locals()[key] = lambda s, prefix=prefix, key=value: _gen(s, prefix, key)

__all__ = list(COMMANDS.keys())