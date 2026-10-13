# Copyright 2019 Ram Rachum and collaborators.
# This program is distributed under the MIT license.

import abc

import sys
from .pycompat import ABC, string_types

MAX_VARIABLE_LENGTH = 100
MAX_EXCEPTION_LENGTH = 200

def _check_methods(C, *methods):
    mro = C.__mro__
    for method in methods:
        for B in mro:
            if method in B.__dict__:
                if B.__dict__[method] is None:
                    return NotImplemented
                break
        else:
            return NotImplemented
    return True


class WritableStream(ABC):
    @abc.abstractmethod
    def write(self, s):
        pass

    @classmethod
    def __subclasshook__(cls, C):
        if cls is WritableStream:
            return _check_methods(C, 'write')
        return NotImplemented



file_reading_errors = (
    IOError,
    OSError,
    ValueError # IronPython weirdness.
)



def shitcode(s):
    return ''.join(
        (c if (0 < ord(c) < 256) else '?') for c in s
    )


def get_repr_function(item, custom_repr):
    for condition, action in custom_repr:
        if isinstance(condition, type):
            condition = lambda x, y=condition: isinstance(x, y)
        if condition(item):
            return action
    return repr


def get_shortish_repr(item, custom_repr=()):
    repr_function = get_repr_function(item, custom_repr)
    try:
        r = repr_function(item)
    except Exception:
        r = 'REPR FAILED'
    r = r.replace('\r', '').replace('\n', '')
    r = truncate(r, MAX_VARIABLE_LENGTH)
    return r


def truncate(string, max_length):
    if len(string) > max_length:
        left = (max_length - 3) // 2
        right = max_length - 3 - left
        string = u'{}...{}'.format(string[:left], string[-right:])
    return string


def ensure_tuple(x):
    if isinstance(x, string_types):
        x = (x,)
    return tuple(x)



