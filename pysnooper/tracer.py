# Copyright 2019 Ram Rachum and collaborators.
# This program is distributed under the MIT license.

import inspect
import sys
import re
import collections
import datetime as datetime_module
import itertools
import threading

from .variables import CommonVariable, Exploding, BaseVariable
from .third_party import six, decorator
from . import utils, pycompat


ipython_filename_pattern = re.compile('^<ipython-input-([0-9]+)-.*>$')


def get_local_reprs(frame, watch=()):
    result = {key: utils.get_shortish_repr(value) for key, value
                                                     in frame.f_locals.items()}
    for variable in watch:
        result.update(variable.items(frame))
    return result


class UnavailableSource(object):
    def __getitem__(self, i):
        return u'SOURCE IS UNAVAILABLE'


source_cache = {}


def get_source_from_frame(frame):
    globs = frame.f_globals or {}
    module_name = globs.get('__name__')
    file_name = frame.f_code.co_filename
    cache_key = (module_name, file_name)
    try:
        return source_cache[cache_key]
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

    source_cache[cache_key] = source
    return source


def get_write_and_truncate_functions(output):
    truncate = None
    if output is None:
        def write(s):
            stderr = sys.stderr
            try:
                stderr.write(s)
            except UnicodeEncodeError:
                # God damn Python 2
                stderr.write(utils.shitcode(s))
    elif isinstance(output, (pycompat.PathLike, str)):
        def write(s):
            with open(six.text_type(output), 'a') as output_file:
                output_file.write(s)

        def truncate():
            with open(six.text_type(output), 'w'):
                pass
    elif callable(output):
        write = output
    else:
        assert isinstance(output, utils.WritableStream)

        def write(s):
            output.write(s)
    return write, truncate


class Tracer:
    def __init__(
            self,
            output=None,
            watch=(),
            watch_explode=(),
            depth=1,
            prefix='',
            overwrite=False,
            thread_info=False,
    ):
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
        '''
        self._write, self.truncate = get_write_and_truncate_functions(output)

        if self.truncate is None and overwrite:
            raise Exception("`overwrite=True` can only be used when writing "
                            "content to file.")
            
        self.watch = [
            v if isinstance(v, BaseVariable) else CommonVariable(v)
            for v in utils.ensure_tuple(watch)
         ] + [
             v if isinstance(v, BaseVariable) else Exploding(v)
             for v in utils.ensure_tuple(watch_explode)
        ]
        self.frame_to_old_local_reprs = collections.defaultdict(lambda: {})
        self.frame_to_local_reprs = collections.defaultdict(lambda: {})
        self.depth = depth
        self.prefix = prefix
        self.overwrite = overwrite
        self._did_overwrite = False
        self.thread_info = thread_info
        self.thread_info_padding = 0
        assert self.depth >= 1
        self.target_codes = set()
        self.target_frames = set()
        self.thread_local = threading.local()

    def __call__(self, function):
        self.target_codes.add(function.__code__)

        def inner(_, *args, **kwargs):
            with self:
                return function(*args, **kwargs)

        return decorator.decorate(function, inner)

    def write(self, s):
        if self.overwrite and not self._did_overwrite:
            self.truncate()
            self._did_overwrite = True
        s = u'{self.prefix}{s}\n'.format(**locals())
        self._write(s)

    def __enter__(self):
        calling_frame = inspect.currentframe().f_back
        if not self._is_internal_frame(calling_frame):
            calling_frame.f_trace = self.trace
            self.target_frames.add(calling_frame)

        stack = self.thread_local.__dict__.setdefault('original_trace_functions', [])
        stack.append(sys.gettrace())
        sys.settrace(self.trace)

    def __exit__(self, exc_type, exc_value, exc_traceback):
        stack = self.thread_local.original_trace_functions
        sys.settrace(stack.pop())
        calling_frame = inspect.currentframe().f_back
        self.target_frames.discard(calling_frame)

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
                        indent = ' ' * 4 * i
                        break
                else:
                    return None
        else:
            indent = ''
        #                                                                     #
        ### Finished checking whether we should trace this line. ##############

        ### Reporting newish and modified variables: ##########################
        #                                                                     #
        self.frame_to_old_local_reprs[frame] = old_local_reprs = \
                                               self.frame_to_local_reprs[frame]
        self.frame_to_local_reprs[frame] = local_reprs = \
                                       get_local_reprs(frame, watch=self.watch)

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
        thread_info = ""
        if self.thread_info:
            current_thread = threading.current_thread()
            thread_info = "{ident}-{name} ".format(
                ident=current_thread.ident, name=current_thread.getName())
        thread_info = self.set_thread_info_padding(thread_info)

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
                    break
        #                                                                     #
        ### Finished dealing with misplaced function definition. ##############

        self.write(u'{indent}{now_string} {thread_info}{event:9} '
                   u'{line_no:4} {source_line}'.format(**locals()))

        if event == 'return':
            return_value_repr = utils.get_shortish_repr(arg)
            self.write('{indent}Return value:.. {return_value_repr}'.
                                                            format(**locals()))

        return self.trace
