# Copyright 2019 Ram Rachum and collaborators.
# This program is distributed under the MIT license.

import abc

from .pycompat import ABC
from .third_party import six

try:
    import reprlib
    import builtins
except ImportError:
    import repr as reprlib
    import __builtin__ as builtins


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


class Repr(reprlib.Repr, object):  # reprlib.Repr is old-style in Python 2
    def __init__(self):
        super(Repr, self).__init__()
        self.maxother = 100

    def repr(self, x):
        try:
            return super(Repr, self).repr(x)
        except Exception as e:
            return '<{} instance at {:#x} (__repr__ raised {})>'.format(
                x.__class__.__name__, id(x), e.__class__.__name__)

    def repr_instance(self, x, level):
        s = builtins.repr(x)
        if len(s) > self.maxother:
            i = max(0, (self.maxother - 3) // 2)
            j = max(0, self.maxother - 3 - i)
            s = s[:i] + '...' + s[len(s) - j:]
        return s


repr_instance = Repr()


def get_shortish_repr(item):
    r = repr_instance.repr(item)
    r = r.replace('\r', '').replace('\n', '')
    return r


def ensure_tuple(x):
    if isinstance(x, six.string_types):
        x = (x,)
    return tuple(x)



