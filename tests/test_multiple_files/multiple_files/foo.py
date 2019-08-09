# Copyright 2019 Ram Rachum and collaborators.
# This program is distributed under the MIT license.

import pysnooper

from .bar import bar_function

@pysnooper.snoop(depth=2)
def foo_function():
    z = bar_function(3)
    return z