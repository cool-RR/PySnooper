# Copyright 2019 Ram Rachum and collaborators.
# This program is distributed under the MIT license.

import collections
import inspect
import sys

from .formatting import Event, VariableEntry, DefaultFormatter

from . import utils, pycompat
from .third_party import six, decorator
from .variables import CommonVariable, Exploding, BaseVariable


def get_local_reprs(frame, watch=()):
    result = {key: utils.get_shortish_repr(value) for key, value
                                                     in frame.f_locals.items()}
    for variable in watch:
        result.update(variable.items(frame))
    return result


class Tracer:
    formatter_class = DefaultFormatter
    
    def __init__(
            self,
            output=None,
            watch=(),
            watch_explode=(),
            depth=1,
            prefix='',
            overwrite=False,
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

        '''
        self.write = self.get_write_function(output, overwrite)
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
        assert self.depth >= 1
        self.target_codes = set()
        self.target_frames = set()
        self.formatter = self.formatter_class(prefix=prefix)

    def get_write_function(self, output, overwrite):
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

    def __call__(self, function):
        self.target_codes.add(function.__code__)

        def inner(_, *args, **kwargs):
            with self:
                return function(*args, **kwargs)

        return decorator.decorate(function, inner)

    def __enter__(self):
        calling_frame = inspect.currentframe().f_back
        if not self._is_internal_frame(calling_frame):
            calling_frame.f_trace = self.trace
            self.target_frames.add(calling_frame)

        self.original_trace_function = sys.gettrace()
        sys.settrace(self.trace)

    def __exit__(self, exc_type, exc_value, exc_traceback):
        sys.settrace(self.original_trace_function)
        calling_frame = inspect.currentframe().f_back
        self.target_frames.discard(calling_frame)

    def _is_internal_frame(self, frame):
        return frame.f_code.co_filename == Tracer.__enter__.__code__.co_filename

    def trace(self, frame, event, arg):

        ### Checking whether we should trace this line: #######################
        #                                                                     #
        # We should trace this line either if it's in the decorated function,
        # or the user asked to go a few levels deeper and we're within that
        # number of levels deeper.

        depth = 0
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
                for depth in range(1, self.depth):
                    _frame_candidate = _frame_candidate.f_back
                    if _frame_candidate is None:
                        return None
                    elif _frame_candidate.f_code in self.target_codes or _frame_candidate in self.target_frames:
                        break
                else:
                    return None
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

        trace_event = Event(frame, event, arg, depth)
        new_variable_type = 'Starting' if event == 'call' else 'New'
        for typ, dct in [(new_variable_type, newish_local_reprs),
                         ('Modified', modified_local_reprs)]:
            for name, value_repr in sorted(dct.items()):
                trace_event.variables.append(VariableEntry(
                    type=typ,
                    name=name,
                    value_repr=value_repr,
                ))
        #                                                                     #
        ### Finished newish and modified variables. ###########################

        formatted = self.formatter.format(trace_event)
        self.write(formatted)

        return self.trace


class FileWriter(object):
    def __init__(self, path, overwrite):
        self.path = six.text_type(path)
        self.overwrite = overwrite

    def write(self, s):
        with open(self.path, 'w' if self.overwrite else 'a') as output_file:
            output_file.write(s)
        self.overwrite = False
