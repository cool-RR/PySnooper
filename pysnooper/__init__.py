# Copyright 2019 Ram Rachum and collaborators.
# This program is distributed under the MIT license.

from .pysnooper import snoop
from .variables import Attrs, Exploded, Indices, Keys
import collections

__VersionInfo = collections.namedtuple('VersionInfo',
                                       ('major', 'minor', 'micro'))

__version__ = '0.0.26'
__version_info__ = __VersionInfo(*(map(int, __version__.split('.'))))

del collections, __VersionInfo # Avoid polluting the namespace
