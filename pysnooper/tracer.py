# Copyright 2019 Ram Rachum and collaborators.
# This program is distributed under the MIT license.

import functools
import inspect
import opcode
import os
import sys
import re
import collections
import datetime as datetime_module
import itertools
import threading
import traceback

from .variables import CommonVariable, Exploding, BaseVariable
from . import utils, pycompat
if pycompat.PY2:
    from io import open


ipython_filename_pattern = re.compile('^<ipython-input-([0-9]+)-.*>$')
ansible_filename_pattern = re.compile(r'^(.+\.zip)[/|\\](ansible[/|\\]modules[/|\\].+\.py)$')
ipykernel_filename_pattern = re.compile(r'^/var/folders/.*/ipykernel_[0-9]+/[0-9]+.py$')
RETURN_OPCODES = {
    'RETURN_GENERATOR', 'RETURN_VALUE', 'RETURN_CONST',
    'INSTRUMENTED_RETURN_GENERATOR', 'INSTRUMENTED_RETURN_VALUE',
    'INSTRUMENTED_RETURN_CONST', 'YIELD_VALUE', 'INSTRUMENTED_YIELD_VALUE'
}


def get_local_reprs(frame, watch=(), custom_repr=(), max_length=None, normalize=False):
    code = frame.f_code
    vars_order = (code.co_varnames + code.co_cellvars + code.co_freevars +
                  tuple(frame.f_locals.keys()))

    result_items = [(key, utils.get_shortish_repr(value, custom_repr,
                                                  max_length, normalize))
                    for key, value in frame.f_locals.items()]
    result_items.sort(key=lambda key_value: vars_order.index(key_value[0]))
    result = collections.OrderedDict(result_items)

    for variable in watch:
        result.update(sorted(variable.items(frame, normalize)))
    return result


class UnavailableSource(object):
    def __getitem__(self, i):
        return u'SOURCE IS UNAVAILABLE'


source_and_path_cache = {}


def get_path_and_source_from_frame(frame):
    globs = frame.f_globals or {}
    module_name = globs.get('__name__')
    file_name = frame.f_code.co_filename
    cache_key = (module_name, file_name)
    try:
        return source_and_path_cache[cache_key]
    except KeyError:
        pass
    loader = globs.get('__loader__')

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
        ansible_filename_match = ansible_filename_pattern.match(file_name)
        ipykernel_filename_match = ipykernel_filename_pattern.match(file_name)
        if ipykernel_filename_match:
            try:
                import linecache
                _, _, source, _ = linecache.cache.get(file_name)
                source = [line.rstrip() for line in source] # remove '\n' at the end
            except Exception:
                pass
        elif ipython_filename_match:
            entry_number = int(ipython_filename_match.group(1))
            try:
                import IPython
                ipython_shell = IPython.get_ipython()
                ((_, _, source_chunk),) = ipython_shell.history_manager. \
                                  get_range(0, entry_number, entry_number + 1)
                source = source_chunk.splitlines()
            except Exception:
                pass
        elif ansible_filename_match:
            try:
                import zipfile
                archive_file = zipfile.ZipFile(ansible_filename_match.group(1), 'r')
                source = archive_file.read(ansible_filename_match.group(2).replace('\\', '/')).splitlines()
            except Exception:
                pass
        else:
            try:
                with open(file_name, 'rb') as fp:
                    source = fp.read().splitlines()
            except utils.file_reading_errors:
                pass
    if not source:
        # We used to check `if source is None` but I found a rare bug where it
        # was empty, but not `None`, so now we check `if not source`.
        source = UnavailableSource()

    # If we just read the source from a file, or if the loader did not
    # apply tokenize.detect_encoding to decode the source into a
    # string, then we should do that ourselves.
    if isinstance(source[0], bytes):
        encoding = 'utf-8'
        for line in source[:2]:
            # File coding may be specified. Match pattern from PEP-263
            # (https://www.python.org/dev/peps/pep-0263/)
            match = re.search(br'coding[:=]\s*([-\w.]+)', line)
            if match:
                encoding = match.group(1).decode('ascii')
                break
        source = [pycompat.text_type(sline, encoding, 'replace') for sline in
                  source]

    result = (file_name, source)
    source_and_path_cache[cache_key] = result
    return result


def get_write_function(output, overwrite):
    is_path = isinstance(output, (pycompat.PathLike, str))
    if overwrite and not is_path:
        raise Exception('`overwrite=True` can only be used when writing '
                        'content to file.')
    if output is None:
        def write(s):
            stderr = sys.stderr
            try:
                stderr.write(s)
            except UnicodeEncodeError:
                # God damn Python 2
                stderr.write(utils.shitcode(s))
    elif is_path:
        return FileWriter(output, overwrite).write
    elif callable(output):
        write = output
    else:
        assert isinstance(output, utils.WritableStream)

        def write(s):
            output.write(s)
    return write


class FileWriter(object):
    def __init__(self, path, overwrite):
        self.path = pycompat.text_type(path)
        self.overwrite = overwrite

    def write(self, s):
        with open(self.path, 'w' if self.overwrite else 'a',
                  encoding='utf-8') as output_file:
            output_file.write(s)
        self.overwrite = False


thread_global = threading.local()
DISABLED = bool(os.getenv('PYSNOOPER_DISABLED', ''))

class Tracer:
    '''
    Snoop on the function, writing everything it's doing to stderr.

    This is useful for debugging.

    When you decorate a function with `@pysnooper.snoop()`
    or wrap a block of code in `with pysnooper.snoop():`, you'll get a log of
    every line that ran in the function and a play-by-play of every local
    variable that changed.

    If stderr is not easily accessible for you, you can redirect the output to
    a file::

        @pysnooper.snoop('/my/log/file.log')

    See values of some expressions that aren't local variables::

        @pysnooper.snoop(watch=('foo.bar', 'self.x["whatever"]'))

    Expand values to see all their attributes or items of lists/dictionaries:

        @pysnooper.snoop(watch_explode=('foo', 'self'))

    (see Advanced Usage in the README for more control)

    Show snoop lines for functions that your function calls::

        @pysnooper.snoop(depth=2)

    Start all snoop lines with a prefix, to grep for them easily::

        @pysnooper.snoop(prefix='ZZZ ')

    On multi-threaded apps identify which thread are snooped in output::

        @pysnooper.snoop(thread_info=True)

    Customize how values are represented as strings::

        @pysnooper.snoop(custom_repr=((type1, custom_repr_func1),
                         (condition2, custom_repr_func2), ...))

    Variables and exceptions get truncated to 100 characters by default. You
    can customize that:

        @pysnooper.snoop(max_variable_length=200)

    You can also use `max_variable_length=None` to never truncate them.

    Show timestamps relative to start time rather than wall time::

        @pysnooper.snoop(relative_time=True)

    The output is colored for easy viewing by default, except on Windows.
    Disable colors like so:

        @pysnooper.snoop(color=False)

    '''
    def __init__(self, output=None, watch=(), watch_explode=(), depth=1,
                 prefix='', overwrite=False, thread_info=False, custom_repr=(),
                 max_variable_length=100, normalize=False, relative_time=False,
                 color=True):
        self._write = get_write_function(output, overwrite)

        self.watch = [
            v if isinstance(v, BaseVariable) else CommonVariable(v)
            for v in utils.ensure_tuple(watch)
         ] + [
             v if isinstance(v, BaseVariable) else Exploding(v)
             for v in utils.ensure_tuple(watch_explode)
        ]
        self.frame_to_local_reprs = {}
        self.start_times = {}
        self.depth = depth
        self.prefix = prefix
        self.thread_info = thread_info
        self.thread_info_padding = 0
        assert self.depth >= 1
        self.target_codes = set()
        self.target_frames = set()
        self.thread_local = threading.local()
        if len(custom_repr) == 2 and not all(isinstance(x,
                      pycompat.collections_abc.Iterable) for x in custom_repr):
            custom_repr = (custom_repr,)
        self.custom_repr = custom_repr
        self.last_source_path = None
        self.max_variable_length = max_variable_length
        self.normalize = normalize
        self.relative_time = relative_time
        self.color = color and sys.platform in ('linux', 'linux2', 'cygwin',
                                                'darwin')

        if self.color:
            self._FOREGROUND_BLUE = '\x1b[34m'
            self._FOREGROUND_CYAN = '\x1b[36m'
            self._FOREGROUND_GREEN = '\x1b[32m'
            self._FOREGROUND_MAGENTA = '\x1b[35m'
            self._FOREGROUND_RED = '\x1b[31m'
            self._FOREGROUND_RESET = '\x1b[39m'
            self._FOREGROUND_YELLOW = '\x1b[33m'
            self._STYLE_BRIGHT = '\x1b[1m'
            self._STYLE_DIM = '\x1b[2m'
            self._STYLE_NORMAL = '\x1b[22m'
            self._STYLE_RESET_ALL = '\x1b[0m'
        else:
            self._FOREGROUND_BLUE = ''
            self._FOREGROUND_CYAN = ''
            self._FOREGROUND_GREEN = ''
            self._FOREGROUND_MAGENTA = ''
            self._FOREGROUND_RED = ''
            self._FOREGROUND_RESET = ''
            self._FOREGROUND_YELLOW = ''
            self._STYLE_BRIGHT = ''
            self._STYLE_DIM = ''
            self._STYLE_NORMAL = ''
            self._STYLE_RESET_ALL = ''

    def __call__(self, function_or_class):
        if DISABLED:
            return function_or_class

        if inspect.isclass(function_or_class):
            return self._wrap_class(function_or_class)
        else:
            return self._wrap_function(function_or_class)

    def _wrap_class(self, cls):
        for attr_name, attr in cls.__dict__.items():
            # Coroutines are functions, but snooping them is not supported
            # at the moment
            if pycompat.iscoroutinefunction(attr):
                continue

            if inspect.isfunction(attr):
                setattr(cls, attr_name, self._wrap_function(attr))
        return cls

    def _wrap_function(self, function):
        self.target_codes.add(function.__code__)

        @functools.wraps(function)
        def simple_wrapper(*args, **kwargs):
            with self:
                return function(*args, **kwargs)

        @functools.wraps(function)
        def generator_wrapper(*args, **kwargs):
            gen = function(*args, **kwargs)
            method, incoming = gen.send, None
            while True:
                with self:
                    try:
                        outgoing = method(incoming)
                    except StopIteration:
                        return
                try:
                    method, incoming = gen.send, (yield outgoing)
                except Exception as e:
                    method, incoming = gen.throw, e

        if pycompat.iscoroutinefunction(function):
            raise NotImplementedError
        if pycompat.isasyncgenfunction(function):
            raise NotImplementedError
        elif inspect.isgeneratorfunction(function):
            return generator_wrapper
        else:
            return simple_wrapper

    def write(self, s):
        s = u'{self.prefix}{s}\n'.format(**locals())
        self._write(s)

    def __enter__(self):
        if DISABLED:
            return
        thread_global.__dict__.setdefault('depth', -1)
        calling_frame = inspect.currentframe().f_back
        if not self._is_internal_frame(calling_frame):
            calling_frame.f_trace = self.trace
            self.target_frames.add(calling_frame)

        stack = self.thread_local.__dict__.setdefault(
            'original_trace_functions', []
        )
        stack.append(sys.gettrace())
        self.start_times[calling_frame] = datetime_module.datetime.now()
        sys.settrace(self.trace)

    def __exit__(self, exc_type, exc_value, exc_traceback):
        if DISABLED:
            return
        stack = self.thread_local.original_trace_functions
        sys.settrace(stack.pop())
        calling_frame = inspect.currentframe().f_back
        self.target_frames.discard(calling_frame)
        self.frame_to_local_reprs.pop(calling_frame, None)

        ### Writing elapsed time: #############################################
        #                                                                     #
        _FOREGROUND_YELLOW = self._FOREGROUND_YELLOW
        _STYLE_DIM = self._STYLE_DIM
        _STYLE_NORMAL = self._STYLE_NORMAL
        _STYLE_RESET_ALL = self._STYLE_RESET_ALL

        start_time = self.start_times.pop(calling_frame)
        duration = datetime_module.datetime.now() - start_time
        elapsed_time_string = pycompat.timedelta_format(duration)
        indent = ' ' * 4 * (thread_global.depth + 1)
        self.write(
            '{indent}{_FOREGROUND_YELLOW}{_STYLE_DIM}'
            'Elapsed time: {_STYLE_NORMAL}{elapsed_time_string}'
            '{_STYLE_RESET_ALL}'.format(**locals())
        )
        #                                                                     #
        ### Finished writing elapsed time. ####################################

    def _is_internal_frame(self, frame):
        return frame.f_code.co_filename == Tracer.__enter__.__code__.co_filename

    def set_thread_info_padding(self, thread_info):
        current_thread_len = len(thread_info)
        self.thread_info_padding = max(self.thread_info_padding,
                                       current_thread_len)
        return thread_info.ljust(self.thread_info_padding)

    def trace(self, frame, event, arg):

        ### Checking whether we should trace this line: #######################
        #                                                                     #
        # We should trace this line either if it's in the decorated function,
        # or the user asked to go a few levels deeper and we're within that
        # number of levels deeper.

        if not (frame.f_code in self.target_codes or frame in self.target_frames):
            if self.depth == 1:
                # We did the most common and quickest check above, because the
                # trace function runs so incredibly often, therefore it's
                # crucial to hyper-optimize it for the common case.
                return None
            elif self._is_internal_frame(frame):
                return None
            else:
                _frame_candidate = frame
                for i in range(1, self.depth):
                    _frame_candidate = _frame_candidate.f_back
                    if _frame_candidate is None:
                        return None
                    elif _frame_candidate.f_code in self.target_codes or _frame_candidate in self.target_frames:
                        break
                else:
                    return None

        #                                                                     #
        ### Finished checking whether we should trace this line. ##############

        if event == 'call':
            thread_global.depth += 1
        indent = ' ' * 4 * thread_global.depth

        _FOREGROUND_BLUE = self._FOREGROUND_BLUE
        _FOREGROUND_CYAN = self._FOREGROUND_CYAN
        _FOREGROUND_GREEN = self._FOREGROUND_GREEN
        _FOREGROUND_MAGENTA = self._FOREGROUND_MAGENTA
        _FOREGROUND_RED = self._FOREGROUND_RED
        _FOREGROUND_RESET = self._FOREGROUND_RESET
        _FOREGROUND_YELLOW = self._FOREGROUND_YELLOW
        _STYLE_BRIGHT = self._STYLE_BRIGHT
        _STYLE_DIM = self._STYLE_DIM
        _STYLE_NORMAL = self._STYLE_NORMAL
        _STYLE_RESET_ALL = self._STYLE_RESET_ALL

        ### Making timestamp: #################################################
        #                                                                     #
        if self.normalize:
            timestamp = ' ' * 15
        elif self.relative_time:
            try:
                start_time = self.start_times[frame]
            except KeyError:
                start_time = self.start_times[frame] = \
                                                 datetime_module.datetime.now()
            duration = datetime_module.datetime.now() - start_time
            timestamp = pycompat.timedelta_format(duration)
        else:
            timestamp = pycompat.time_isoformat(
                datetime_module.datetime.now().time(),
                timespec='microseconds'
            )
        #                                                                     #
        ### Finished making timestamp. ########################################

        line_no = frame.f_lineno
        source_path, source = get_path_and_source_from_frame(frame)
        source_path = source_path if not self.normalize else os.path.basename(source_path)
        if self.last_source_path != source_path:
            self.write(u'{_FOREGROUND_YELLOW}{_STYLE_DIM}{indent}Source path:... '
                       u'{_STYLE_NORMAL}{source_path}'
                       u'{_STYLE_RESET_ALL}'.format(**locals()))
            self.last_source_path = source_path
        source_line = source[line_no - 1]
        thread_info = ""
        if self.thread_info:
            if self.normalize:
                raise NotImplementedError("normalize is not supported with "
                                          "thread_info")
            current_thread = threading.current_thread()
            thread_info = "{ident}-{name} ".format(
                ident=current_thread.ident, name=current_thread.name)
        thread_info = self.set_thread_info_padding(thread_info)

        ### Reporting newish and modified variables: ##########################
        #                                                                     #
        old_local_reprs = self.frame_to_local_reprs.get(frame, {})
        self.frame_to_local_reprs[frame] = local_reprs = \
                                       get_local_reprs(frame,
                                                       watch=self.watch, custom_repr=self.custom_repr,
                                                       max_length=self.max_variable_length,
                                                       normalize=self.normalize,
                                                       )

        newish_string = ('Starting var:.. ' if event == 'call' else
                                                            'New var:....... ')

        for name, value_repr in local_reprs.items():
            if name not in old_local_reprs:
                self.write('{indent}{_FOREGROUND_GREEN}{_STYLE_DIM}'
                           '{newish_string}{_STYLE_NORMAL}{name} = '
                           '{value_repr}{_STYLE_RESET_ALL}'.format(**locals()))
            elif old_local_reprs[name] != value_repr:
                self.write('{indent}{_FOREGROUND_GREEN}{_STYLE_DIM}'
                           'Modified var:.. {_STYLE_NORMAL}{name} = '
                           '{value_repr}{_STYLE_RESET_ALL}'.format(**locals()))

        #                                                                     #
        ### Finished newish and modified variables. ###########################


        ### Dealing with misplaced function definition: #######################
        #                                                                     #
        if event == 'call' and source_line.lstrip().startswith('@'):
            # If a function decorator is found, skip lines until an actual
            # function definition is found.
            for candidate_line_no in itertools.count(line_no):
                try:
                    candidate_source_line = source[candidate_line_no - 1]
                except IndexError:
                    # End of source file reached without finding a function
                    # definition. Fall back to original source line.
                    break

                if candidate_source_line.lstrip().startswith('def'):
                    # Found the def line!
                    line_no = candidate_line_no
                    source_line = candidate_source_line
                    break
        #                                                                     #
        ### Finished dealing with misplaced function definition. ##############

        # If a call ends due to an exception, we still get a 'return' event
        # with arg = None. This seems to be the only way to tell the difference
        # https://stackoverflow.com/a/12800909/2482744
        code_byte = frame.f_code.co_code[frame.f_lasti]
        if not isinstance(code_byte, int):
            code_byte = ord(code_byte)
        ended_by_exception = (
                event == 'return'
                and arg is None
                and opcode.opname[code_byte] not in RETURN_OPCODES
        )

        if ended_by_exception:
            self.write('{_FOREGROUND_RED}{indent}Call ended by exception{_STYLE_RESET_ALL}'.
                       format(**locals()))
        else:
            self.write(u'{indent}{_STYLE_DIM}{timestamp} {thread_info}{event:9} '
                       u'{line_no:4}{_STYLE_RESET_ALL} {source_line}'.format(**locals()))

        if event == 'return':
            self.frame_to_local_reprs.pop(frame, None)
            self.start_times.pop(frame, None)
            thread_global.depth -= 1

            if not ended_by_exception:
                return_value_repr = utils.get_shortish_repr(arg,
                                                            custom_repr=self.custom_repr,
                                                            max_length=self.max_variable_length,
                                                            normalize=self.normalize,
                                                            )
                self.write('{indent}{_FOREGROUND_CYAN}{_STYLE_DIM}'
                           'Return value:.. {_STYLE_NORMAL}{return_value_repr}'
                           '{_STYLE_RESET_ALL}'.
                           format(**locals()))

        if event == 'exception':
            exception = '\n'.join(traceback.format_exception_only(*arg[:2])).strip()
            if self.max_variable_length:
                exception = utils.truncate(exception, self.max_variable_length)
            self.write('{indent}{_FOREGROUND_RED}Exception:..... '
                       '{_STYLE_BRIGHT}{exception}'
                       '{_STYLE_RESET_ALL}'.format(**locals()))

        return self.trace
