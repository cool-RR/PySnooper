# Copyright 2019 Ram Rachum and collaborators.
# This program is distributed under the MIT license.
'''
PySnooper - Never use print for debugging again

Usage:

    import pysnooper

    @pysnooper.snoop()
    def your_function(x):
        ...

A log will be written to stderr showing the lines executed and variables
changed in the decorated function.

For more information, see https://github.com/cool-RR/PySnooper
'''

from .tracer import Tracer as snoop
from .variables import Attrs, Exploding, Indices, Keys
import collections

__VersionInfo = collections.namedtuple('VersionInfo',
                                       ('major', 'minor', 'micro'))

__version__ = '1.0.0'
__version_info__ = __VersionInfo(*(map(int, __version__.split('.'))))

del collections, __VersionInfo # Avoid polluting the namespace
