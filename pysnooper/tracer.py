# Copyright 2019 Ram Rachum.
# This program is distributed under the MIT license.

import types
import sys
import re
import collections
import datetime as datetime_module

import six

MAX_VARIABLE_LENGTH = 100

def get_shortish_repr(item):
    r = repr(item)
    if len(r) > MAX_VARIABLE_LENGTH:
        r = '{truncated_r}...'.format(truncated_r=r[:MAX_VARIABLE_LENGTH])
    return r

def get_local_reprs(frame, variables=()):
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


source_cache_by_module_name = {}
source_cache_by_file_name = {}
def get_source_from_frame(frame):
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

    source = None
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
        source = [six.text_type(sline, encoding, 'replace') for sline in
                  source]

    if module_name:
        source_cache_by_module_name[module_name] = source
    if file_name:
        source_cache_by_file_name[file_name] = source
    return source

class Tracer:
    def __init__(self, target_code_object, write, variables=(), depth=1,
                 prefix=''):
        self.target_code_object = target_code_object
        self._write = write
        self.variables = variables
        self.frame_to_old_local_reprs = collections.defaultdict(lambda: {})
        self.frame_to_local_reprs = collections.defaultdict(lambda: {})
        self.depth = depth
        self.prefix = prefix
        assert self.depth >= 1

    def write(self, s):
        s = '{self.prefix}{s}\n'.format(**locals())
        if isinstance(s, bytes): # Python 2 compatibility
            s = s.decode()
        self._write(s)

    def __enter__(self):
        self.original_trace_function = sys.gettrace()
        sys.settrace(self.trace)

    def __exit__(self, exc_type, exc_value, exc_traceback):
        sys.settrace(self.original_trace_function)


    def trace(self, frame, event, arg):

        ### Checking whether we should trace this line: #######################
        #                                                                     #
        # We should trace this line either if it's in the decorated function,
        # or the user asked to go a few levels deeper and we're within that
        # number of levels deeper.

        if frame.f_code is not self.target_code_object:
            if self.depth == 1:
                # We did the most common and quickest check above, because the
                # trace function runs so incredibly often, therefore it's
                # crucial to hyper-optimize it for the common case.
                return self.trace
            else:
                _frame_candidate = frame
                for i in range(1, self.depth):
                    _frame_candidate = _frame_candidate.f_back
                    if _frame_candidate is None:
                        return self.trace
                    elif _frame_candidate.f_code is self.target_code_object:
                        indent = ' ' * 4 * i
                        break
                else:
                    return self.trace
        else:
            indent = ''
        #                                                                     #
        ### Finished checking whether we should trace this line. ##############

        ### Reporting newish and modified variables: ##########################
        #                                                                     #
        self.frame_to_old_local_reprs[frame] = old_local_reprs = \
                                               self.frame_to_local_reprs[frame]
        self.frame_to_local_reprs[frame] = local_reprs = \
                               get_local_reprs(frame, variables=self.variables)

        modified_local_reprs = {}
        newish_local_reprs = {}

        for key, value in local_reprs.items():
            if key not in old_local_reprs:
                newish_local_reprs[key] = value
            elif old_local_reprs[key] != value:
                modified_local_reprs[key] = value

        newish_string = ('Starting var:.. ' if event == 'call' else
                                                            'New var:....... ')
        for name, value_repr in newish_local_reprs.items():
            self.write('{indent}{newish_string}{name} = {value_repr}'.format(
                                                                   **locals()))
        for name, value_repr in modified_local_reprs.items():
            self.write('{indent}Modified var:.. {name} = {value_repr}'.format(
                                                                   **locals()))
        #                                                                     #
        ### Finished newish and modified variables. ###########################

        now_string = datetime_module.datetime.now().time().isoformat()
        source_line = get_source_from_frame(frame)[frame.f_lineno - 1]
        self.write('{indent}{now_string} {event:9} '
                   '{frame.f_lineno:4} {source_line}'.format(**locals()))
        return self.trace


