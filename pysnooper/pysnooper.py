# Copyright 2019 Ram Rachum.
# This program is distributed under the MIT license.

from __future__ import annotations

import sys
import os
import pathlib
import inspect
import types
import typing
import datetime as datetime_module
import re
import collections

import decorator

from . import utils

        
def get_write_function(output) -> typing.Callable:
    if output is None:
        def write(s):
            stderr = sys.stderr
            stderr.write(s)
            stderr.write('\n')
    elif isinstance(output, (os.PathLike, str)):
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
    
    
class Tracer:
    def __init__(self, target_code_object: types.CodeType, write: callable, *,
                 variables: typing.Sequence=()):
        self.target_code_object = target_code_object
        self.write = write
        self.variables = variables
        self.old_local_reprs = {}
        self.local_reprs = {}
        
        
    def __enter__(self):
        self.original_trace_function = sys.gettrace()
        sys.settrace(self.trace)
        
    def __exit__(self, exc_type, exc_value, exc_traceback):
        sys.settrace(self.original_trace_function)
        
    def trace(self: Tracer, frame: types.FrameType, event: str,
              arg: typing.Any) -> typing.Callable:
        if frame.f_code != self.target_code_object:
            return self.trace
        self.old_local_reprs, self.local_reprs = \
             self.local_reprs, get_local_reprs(frame, variables=self.variables)
        modified_local_reprs = {
            key: value for key, value in self.local_reprs.items()
            if (key not in self.old_local_reprs) or
                                           (self.old_local_reprs[key] != value)
        }
        for name, value_repr in modified_local_reprs.items():
            self.write(f'            ==> {name} = {value_repr}')
        # x = repr((frame.f_code.co_stacksize, frame, event, arg))
        now_string = datetime_module.datetime.now().time().isoformat()
        source_line = get_source_from_frame(frame)[frame.f_lineno - 1]
        self.write(f'{now_string} {event:9} '
                   f'{frame.f_lineno:4} {source_line}')
        return self.trace
        
        
        
source_cache_by_module_name = {}
source_cache_by_file_name = {}
def get_source_from_frame(frame: types.FrameType) -> str:
    module_name = frame.f_globals.get('__name__') or ''
    if module_name:
        try:
            return source_cache_by_module_name[module_name]
        except KeyError:
            pass
    file_name = frame.f_code.co_filename
    if file_name:
        try:
            return source_cache_by_file_name[file_name]
        except KeyError:
            pass
    function = frame.f_code.co_name
    loader = frame.f_globals.get('__loader__')
    
    source: typing.Union[None, str] = None
    if hasattr(loader, 'get_source'):
        try:
            source = loader.get_source(module_name)
        except ImportError:
            pass
        if source is not None:
            source = source.splitlines()
    if source is None:
        try:
            with open(file_name, 'rb') as fp:
                source = fp.read().splitlines()
        except (OSError, IOError):
            pass
    if source is None:
        raise NotImplementedError

    # If we just read the source from a file, or if the loader did not
    # apply tokenize.detect_encoding to decode the source into a
    # string, then we should do that ourselves.
    if isinstance(source[0], bytes):
        encoding = 'ascii'
        for line in source[:2]:
            # File coding may be specified. Match pattern from PEP-263
            # (https://www.python.org/dev/peps/pep-0263/)
            match = re.search(br'coding[:=]\s*([-\w.]+)', line)
            if match:
                encoding = match.group(1).decode('ascii')
                break
        source = [str(sline, encoding, 'replace') for sline in source]

    if module_name:
        source_cache_by_module_name[module_name] = source
    if file_name:
        source_cache_by_file_name[file_name] = source
    return source

def get_local_reprs(frame: types.FrameType, *, variables: typing.Sequence=()) -> dict:
    result = {}
    for key, value in frame.f_locals.items():
        try:
            result[key] = get_shortish_repr(value)
        except Exception:
            continue
    locals_and_globals = collections.ChainMap(frame.f_locals, frame.f_globals)
    for variable in variables:
        steps = variable.split('.')
        step_iterator = iter(steps)
        try:
            current = locals_and_globals[next(step_iterator)]
            for step in step_iterator:
                current = getattr(current, step)
        except (KeyError, AttributeError):
            continue
        try:
            result[variable] = get_shortish_repr(current)
        except Exception:
            continue
    return result

def get_shortish_repr(item) -> str:
    r = repr(item)
    if len(r) > 100:
        r = f'{r[:97]}...'
    return r


def snoop(output=None, *, variables=()) -> typing.Callable:
    write = get_write_function(output)
    @decorator.decorator
    def decorate(function, *args, **kwargs) -> typing.Callable:
        target_code_object = function.__code__
        with Tracer(target_code_object, write, variables=variables):
            return function(*args, **kwargs)
    
    return decorate
    
    
    