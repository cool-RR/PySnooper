# Copyright 2019 Ram Rachum and collaborators.
# This program is distributed under the MIT license.

import sys
import re
import collections
import datetime as datetime_module
import itertools
try:
    import reprlib
    import builtins
except ImportError:
    import repr as reprlib
    import __builtin__ as builtins

from .third_party import six
from . import utils

ipython_filename_pattern = re.compile('^<ipython-input-([0-9]+)-.*>$')


class Repr(reprlib.Repr, object):  # reprlib.Repr is old-style in Python 2
    def __init__(self):
        super(Repr, self).__init__()
        self.maxother = 100

    def repr(self, x):
        try:
            return super(Repr, self).repr(x)
        except Exception as e:
            return '<{} instance at {:#x} (__repr__ raised {})>'.format(
                x.__class__.__name__, id(x), e.__class__.__name__)

    def repr_instance(self, x, level):
        s = builtins.repr(x)
        if len(s) > self.maxother:
            i = max(0, (self.maxother - 3) // 2)
            j = max(0, self.maxother - 3 - i)
            s = s[:i] + '...' + s[len(s) - j:]
        return s


repr_instance = Repr()


def get_shortish_repr(item):
    r = repr_instance.repr(item)
    r = r.replace('\r', '').replace('\n', '')
    return r


def get_local_reprs(frame, variables=()):
    result = {key: get_shortish_repr(value) for key, value
                                                     in frame.f_locals.items()}
    for variable in variables:
        try:
            result[variable] = get_shortish_repr(
                eval(variable, (frame.f_globals or {}), frame.f_locals)
            )
        except Exception:
            pass
    return result


class UnavailableSource(object):
    def __getitem__(self, i):
        return u'SOURCE IS UNAVAILABLE'


source_cache_by_module_name = {}
source_cache_by_file_name = {}


def get_source_from_frame(frame):
    module_name = (frame.f_globals or {}).get('__name__') or ''
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
    loader = (frame.f_globals or {}).get('__loader__')

    source = None
    if hasattr(loader, 'get_source'):
        try:
            source = loader.get_source(module_name)
        except ImportError:
            pass
        if source is not None:
            source = source.splitlines()
    if source is None:
        ipython_filename_match = ipython_filename_pattern.match(file_name)
        if ipython_filename_match:
            entry_number = int(ipython_filename_match.group(1))
            try:
                import IPython
                ipython_shell = IPython.get_ipython()
                ((_, _, source_chunk),) = ipython_shell.history_manager. \
                                  get_range(0, entry_number, entry_number + 1)
                source = source_chunk.splitlines()
            except Exception:
                pass
        else:
            try:
                with open(file_name, 'rb') as fp:
                    source = fp.read().splitlines()
            except utils.file_reading_errors:
                pass
    if source is None:
        source = UnavailableSource()

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
    def __init__(self, target_code_object, write, truncate, variables=(),
                 depth=1, prefix='', overwrite=False):
        self.target_code_object = target_code_object
        self._write = write
        self.truncate = truncate
        if isinstance(variables, six.string_types):
            variables = (variables,)
        self.variables = variables
        self.frame_to_old_local_reprs = collections.defaultdict(lambda: {})
        self.frame_to_local_reprs = collections.defaultdict(lambda: {})
        self.depth = depth
        self.prefix = prefix
        self.overwrite = overwrite
        self._did_overwrite = False
        assert self.depth >= 1

    def write(self, s):
        if self.overwrite and not self._did_overwrite:
            self.truncate()
            self._did_overwrite = True
        s = u'{self.prefix}{s}\n'.format(**locals())
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
        for name, value_repr in sorted(newish_local_reprs.items()):
            self.write('{indent}{newish_string}{name} = {value_repr}'.format(
                                                                   **locals()))
        for name, value_repr in sorted(modified_local_reprs.items()):
            self.write('{indent}Modified var:.. {name} = {value_repr}'.format(
                                                                   **locals()))
        #                                                                     #
        ### Finished newish and modified variables. ###########################

        now_string = datetime_module.datetime.now().time().isoformat()
        line_no = frame.f_lineno
        source_line = get_source_from_frame(frame)[line_no - 1]

        ### Dealing with misplaced function definition: #######################
        #                                                                     #
        if event == 'call' and source_line.lstrip().startswith('@'):
            # If a function decorator is found, skip lines until an actual
            # function definition is found.
            for candidate_line_no in itertools.count(line_no):
                try:
                    candidate_source_line = \
                            get_source_from_frame(frame)[candidate_line_no - 1]
                except IndexError:
                    # End of source file reached without finding a function
                    # definition. Fall back to original source line.
                    break

                if candidate_source_line.lstrip().startswith('def'):
                    # Found the def line!
                    line_no = candidate_line_no
                    source_line = candidate_source_line
                    file_name = (frame.f_code.co_filename if self.depth>=2 else '')
                    self.write('In file:.. {file_name}'.format(**locals()))
                    break
        #                                                                     #
        ### Finished dealing with misplaced function definition. ##############

        self.write(u'{indent}{now_string} {event:9} '
                   u'{line_no:4} {source_line}'.format(**locals()))

        if event == 'return':
            return_value_repr = get_shortish_repr(arg)
            self.write('{indent}Return value:.. {return_value_repr}'.
                                                            format(**locals()))

        return self.trace
