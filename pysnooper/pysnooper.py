# Copyright 2019 Ram Rachum.
# This program is distributed under the MIT license.

import sys
import os
import pathlib
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
            stderr.write('\n')
    elif isinstance(output, (pycompat.PathLike, str)):
        output_path = pathlib.Path(output)
        def write(s):
            with output_path.open('a') as output_file:
                output_file.write(s)
                output_file.write('\n')
    else:
        assert isinstance(output, utils.WritableStream)
        def write(s):
            output.write(s)
            output.write('\n')
            
    return write
    
    

def snoop(output=None, *, variables=(), depth=1):
    write = get_write_function(output)
    @decorator.decorator
    def decorate(function, *args, **kwargs):
        target_code_object = function.__code__
        with Tracer(target_code_object=target_code_object,
                    write=write, variables=variables,
                    depth=depth):
            return function(*args, **kwargs)
    
    return decorate
    
    
    