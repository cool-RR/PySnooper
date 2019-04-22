# Copyright 2019 Ram Rachum.
# This program is distributed under the MIT license.

import sys
import os
import inspect
import types
import datetime as datetime_module
import re
import collections

import decorator

from . import utils
from . import pycompat
from .tracer import Tracer


def get_write_function(output):
    if output is None:
        def write(s):
            stderr = sys.stderr
            stderr.write(s)
    elif isinstance(output, (pycompat.PathLike, str)):
        def write(s):
            with open(output_path, 'a') as output_file:
                output_file.write(s)
    else:
        assert isinstance(output, utils.WritableStream)
        def write(s):
            output.write(s)

    return write



def snoop(output=None, variables=(), depth=1, prefix=''):
    '''
    Snoop on the function, writing everything it's doing to stderr.

    This is useful for debugging.

    When you decorate a function with `@pysnooper.snoop()`, you'll get a log of
    every line that ran in the function and a play-by-play of every local
    variable that changed.

    If stderr is not easily accessible for you, you can redirect the output to
    a file::

        @pysnooper.snoop('/my/log/file.log')

    See values of some variables that aren't local variables::

        @pysnooper.snoop(variables=('foo.bar', 'self.whatever'))

    Show snoop lines for functions that your function calls::

        @pysnooper.snoop(depth=2)

    Start all snoop lines with a prefix, to grep for them easily::

        @pysnooper.snoop(prefix='ZZZ ')

    '''
    write = get_write_function(output)
    @decorator.decorator
    def decorate(function, *args, **kwargs):
        target_code_object = function.__code__
        with Tracer(target_code_object=target_code_object,
                    write=write, variables=variables,
                    depth=depth, prefix=prefix):
            return function(*args, **kwargs)

    return decorate


