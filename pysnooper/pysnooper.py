# Copyright 2019 Ram Rachum and collaborators.
# This program is distributed under the MIT license.

import sys

from .third_party import decorator

from . import utils
from . import pycompat
from .tracer import Tracer


def get_write_and_truncate_functions(output):
    if output is None:
        def write(s):
            stderr = sys.stderr
            try:
                stderr.write(s)
            except UnicodeEncodeError:
                 # God damn Python 2
                stderr.write(utils.shitcode(s))
        truncate = None
    elif isinstance(output, (pycompat.PathLike, str)):
        def write(s):
            with open(output, 'a') as output_file:
                output_file.write(s)
        def truncate():
            with open(output, 'w') as output_file:
                pass
    elif callable(output):
        write = output
        truncate = None
    else:
        assert isinstance(output, utils.WritableStream)
        def write(s):
            output.write(s)
        truncate = None

    return (write, truncate)


def snoop(output=None, variables=(), exploded_variables=(), depth=1, prefix='', overwrite=False):
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

    Expand values to see all their attributes or items of lists/dictionaries:

        @pysnooper.snoop(exploding_variables=('foo', 'self'))

    (see Advanced Usage in the README for more control)

    Show snoop lines for functions that your function calls::

        @pysnooper.snoop(depth=2)

    Start all snoop lines with a prefix, to grep for them easily::

        @pysnooper.snoop(prefix='ZZZ ')

    '''
    write, truncate = get_write_and_truncate_functions(output)
    if truncate is None and overwrite:
        raise Exception("`overwrite=True` can only be used when writing "
                        "content to file.")
    def decorate(function):
        target_code_object = function.__code__
        tracer = Tracer(target_code_object=target_code_object, write=write,
                        truncate=truncate, variables=variables, depth=depth,
                        prefix=prefix, overwrite=overwrite,
                        exploded_variables=exploded_variables)

        def inner(function_, *args, **kwargs):
            with tracer:
                return function(*args, **kwargs)
        return decorator.decorate(function, inner)

    return decorate
