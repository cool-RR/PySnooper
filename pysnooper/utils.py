# Copyright 2019 Ram Rachum and collaborators.
# This program is distributed under the MIT license.

import abc

from .pycompat import ABC
from .third_party import six

MAX_VARIABLE_LENGTH = 100

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


def get_shortish_repr(item):
    try:
        r = repr(item)
    except Exception:
        r = 'REPR FAILED'
    r = r.replace('\r', '').replace('\n', '')
    if len(r) > MAX_VARIABLE_LENGTH:
        r = '{truncated_r}...'.format(truncated_r=r[:MAX_VARIABLE_LENGTH])
    return r



def ensure_tuple(x):
    if isinstance(x, six.string_types):
        x = (x,)
    return tuple(x)



