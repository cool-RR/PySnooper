# Copyright 2019 Ram Rachum and collaborators.
# This program is distributed under the MIT license.

from .pysnooper import snoop
import collections

__VersionInfo = collections.namedtuple('VersionInfo',
                                       ('major', 'minor', 'micro'))

__version_info__ = __VersionInfo(0, 0, 17)
__version__ = '.'.join(map(str, __version_info__))

del collections, __VersionInfo # Avoid polluting the namespace
