# Copyright 2019 Ram Rachum and collaborators.
# This program is distributed under the MIT license.
import os
import re
import abc
import inspect
import sys

from pysnooper.utils import DEFAULT_REPR_RE

try:
    from itertools import zip_longest
except ImportError:
    from itertools import izip_longest as zip_longest

from . import mini_toolbox

import pysnooper.pycompat


def get_function_arguments(function, exclude=()):
    try:
        getfullargspec = inspect.getfullargspec
    except AttributeError:
        result = inspect.getargspec(function).args
    else:
        result = getfullargspec(function).args
    for exclude_item in exclude:
        result.remove(exclude_item)
    return result


class _BaseEntry(pysnooper.pycompat.ABC):
    def __init__(self, prefix='', min_python_version=None, max_python_version=None):
        self.prefix = prefix
        self.min_python_version = min_python_version
        self.max_python_version = max_python_version

    @abc.abstractmethod
    def check(self, s):
        pass

    def is_compatible_with_current_python_version(self):
        compatible = True
        if self.min_python_version and self.min_python_version > sys.version_info:
            compatible = False
        if self.max_python_version and self.max_python_version < sys.version_info:
            compatible = False

        return compatible

    def __repr__(self):
        init_arguments = get_function_arguments(self.__init__,
                                                exclude=('self',))
        attributes = {
            key: repr(getattr(self, key)) for key in init_arguments
                                              if getattr(self, key) is not None
        }
        return '%s(%s)' % (
            type(self).__name__,
            ', '.join('{key}={value}'.format(**locals()) for key, value
                                                         in attributes.items())
        )



class _BaseValueEntry(_BaseEntry):
    def __init__(self, prefix='', min_python_version=None,
                 max_python_version=None):
        _BaseEntry.__init__(self, prefix=prefix,
                            min_python_version=min_python_version,
                            max_python_version=max_python_version)
        self.line_pattern = re.compile(
            r"""^%s(?P<indent>(?: {4})*)(?P<preamble>[^:]*):"""
            r"""\.{2,7} (?P<content>.*)$""" % (re.escape(self.prefix),)
        )

    @abc.abstractmethod
    def _check_preamble(self, preamble):
        pass

    @abc.abstractmethod
    def _check_content(self, preamble):
        pass

    def check(self, s):
        match = self.line_pattern.match(s)
        if not match:
            return False
        _, preamble, content = match.groups()
        return (self._check_preamble(preamble) and
                                                  self._check_content(content))


class ElapsedTimeEntry(_BaseEntry):
    def __init__(self, elapsed_time_value=None, tolerance=0.2, prefix='',
                 min_python_version=None, max_python_version=None):
        _BaseEntry.__init__(self, prefix=prefix,
                            min_python_version=min_python_version,
                            max_python_version=max_python_version)
        self.line_pattern = re.compile(
            r"""^%s(?P<indent>(?: {4})*)Elapsed time: (?P<time>.*)""" % (
                re.escape(self.prefix),
            )
        )
        self.elapsed_time_value = elapsed_time_value
        self.tolerance = tolerance

    def check(self, s):
        match = self.line_pattern.match(s)
        if not match:
            return False
        timedelta = pysnooper.pycompat.timedelta_parse(match.group('time'))
        if self.elapsed_time_value:
            return abs(timedelta.total_seconds() - self.elapsed_time_value) \
                                                              <= self.tolerance
        else:
            return True



class CallEndedByExceptionEntry(_BaseEntry):
    # Todo: Looking at this class, we could rework the hierarchy.
    def __init__(self, prefix=''):
        _BaseEntry.__init__(self, prefix=prefix)

    def check(self, s):
        return re.match(
            r'''(?P<indent>(?: {4})*)Call ended by exception''',
            s
        )



class VariableEntry(_BaseValueEntry):
    def __init__(self, name=None, value=None, stage=None, prefix='',
                 name_regex=None, value_regex=None, min_python_version=None,
                 max_python_version=None):
        _BaseValueEntry.__init__(self, prefix=prefix,
                                 min_python_version=min_python_version,
                                 max_python_version=max_python_version)
        if name is not None:
            assert name_regex is None
        if value is not None:
            assert value_regex is None
        assert stage in (None, 'starting', 'new', 'modified')

        self.name = name
        self.value = value
        self.stage = stage
        self.name_regex = (None if name_regex is None else
                           re.compile(name_regex))
        self.value_regex = (None if value_regex is None else
                            re.compile(value_regex))

    _preamble_pattern = re.compile(
        r"""^(?P<stage>New|Modified|Starting) var$"""
    )

    def _check_preamble(self, preamble):
        match = self._preamble_pattern.match(preamble)
        if not match:
            return False
        stage = match.group('stage')
        return self._check_stage(stage)

    _content_pattern = re.compile(
        r"""^(?P<name>.+?) = (?P<value>.+)$"""
    )

    def _check_content(self, content):
        match = self._content_pattern.match(content)
        if not match:
            return False
        name, value = match.groups()
        return self._check_name(name) and self._check_value(value)

    def _check_name(self, name):
        if self.name is not None:
            return name == self.name
        elif self.name_regex is not None:
            return self.name_regex.match(name)
        else:
            return True

    def _check_value(self, value):
        if self.value is not None:
            return value == self.value
        elif self.value_regex is not None:
            return self.value_regex.match(value)
        else:
            return True

    def _check_stage(self, stage):
        stage = stage.lower()
        if self.stage is None:
            return stage in ('starting', 'new', 'modified')
        else:
            return stage == self.stage


class _BaseSimpleValueEntry(_BaseValueEntry):
    def __init__(self, value=None, value_regex=None, prefix='',
                 min_python_version=None, max_python_version=None):
        _BaseValueEntry.__init__(self, prefix=prefix,
                                 min_python_version=min_python_version,
                                 max_python_version=max_python_version)
        if value is not None:
            assert value_regex is None

        self.value = value
        self.value_regex = (None if value_regex is None else
                            re.compile(value_regex))

    def _check_preamble(self, preamble):
        return bool(self._preamble_pattern.match(preamble))

    def _check_content(self, content):
        return self._check_value(content)

    def _check_value(self, value):
        if self.value is not None:
            return value == self.value
        elif self.value_regex is not None:
            return self.value_regex.match(value)
        else:
            return True

class ReturnValueEntry(_BaseSimpleValueEntry):
    _preamble_pattern = re.compile(
        r"""^Return value$"""
    )

class ExceptionValueEntry(_BaseSimpleValueEntry):
    _preamble_pattern = re.compile(
        r"""^Exception$"""
    )

class SourcePathEntry(_BaseValueEntry):
    def __init__(self, source_path=None, source_path_regex=None, prefix=''):
        _BaseValueEntry.__init__(self, prefix=prefix)
        if source_path is not None:
            assert source_path_regex is None

        self.source_path = source_path
        self.source_path_regex = (None if source_path_regex is None else
                            re.compile(source_path_regex))

    _preamble_pattern = re.compile(
        r"""^Source path$"""
    )

    def _check_preamble(self, preamble):
        return bool(self._preamble_pattern.match(preamble))

    def _check_content(self, source_path):
        if self.source_path is not None:
            return source_path == self.source_path
        elif self.source_path_regex is not None:
            return self.source_path_regex.match(source_path)
        else:
            return True


class _BaseEventEntry(_BaseEntry):
    def __init__(self, source=None, source_regex=None, thread_info=None,
                 thread_info_regex=None, prefix='', min_python_version=None,
                 max_python_version=None):
        _BaseEntry.__init__(self, prefix=prefix,
                            min_python_version=min_python_version,
                            max_python_version=max_python_version)
        if type(self) is _BaseEventEntry:
            raise TypeError
        if source is not None:
            assert source_regex is None
        self.line_pattern = re.compile(
            r"""^%s(?P<indent>(?: {4})*)(?:(?:[0-9:.]{15})|(?: {15})) """
            r"""(?P<thread_info>[0-9]+-[0-9A-Za-z_-]+[ ]+)?"""
            r"""(?P<event_name>[a-z_]*) +(?P<line_number>[0-9]*) """
            r"""+(?P<source>.*)$""" % (re.escape(self.prefix,))
        )

        self.source = source
        self.source_regex = (None if source_regex is None else
                             re.compile(source_regex))
        self.thread_info = thread_info
        self.thread_info_regex = (None if thread_info_regex is None else
                             re.compile(thread_info_regex))

    @property
    def event_name(self):
        return re.match('^[A-Z][a-z_]*', type(self).__name__).group(0).lower()

    def _check_source(self, source):
        if self.source is not None:
            return source == self.source
        elif self.source_regex is not None:
            return self.source_regex.match(source)
        else:
            return True

    def _check_thread_info(self, thread_info):
        if self.thread_info is not None:
            return thread_info == self.thread_info
        elif self.thread_info_regex is not None:
            return self.thread_info_regex.match(thread_info)
        else:
            return True

    def check(self, s):
        match = self.line_pattern.match(s)
        if not match:
            return False
        _, thread_info, event_name, _, source = match.groups()
        return (event_name == self.event_name and
                self._check_source(source) and
                self._check_thread_info(thread_info))


class CallEntry(_BaseEventEntry):
    pass


class LineEntry(_BaseEventEntry):
    pass


class ReturnEntry(_BaseEventEntry):
    pass


class ExceptionEntry(_BaseEventEntry):
    pass


class OpcodeEntry(_BaseEventEntry):
    pass


class OutputFailure(Exception):
    pass


def verify_normalize(lines, prefix):
    time_re = re.compile(r"[0-9:.]{15}")
    src_re = re.compile(r'^(?: *)Source path:\.\.\. (.*)$')
    for line in lines:
        if DEFAULT_REPR_RE.search(line):
            msg = "normalize is active, memory address should not appear"
            raise OutputFailure(line, msg)
        no_prefix = line.replace(prefix if prefix else '', '').strip()
        if time_re.match(no_prefix):
            msg = "normalize is active, time should not appear"
            raise OutputFailure(line, msg)
        m = src_re.match(line)
        if m:
            if not os.path.basename(m.group(1)) == m.group(1):
                msg = "normalize is active, path should be only basename"
                raise OutputFailure(line, msg)


def assert_output(output, expected_entries, prefix=None, normalize=False):
    lines = tuple(filter(None, output.split('\n')))
    if expected_entries and not lines:
        raise OutputFailure("Output is empty")

    if prefix is not None:
        for line in lines:
            if not line.startswith(prefix):
                raise OutputFailure(line)

    if normalize:
        verify_normalize(lines, prefix)

    # Filter only entries compatible with the current Python
    filtered_expected_entries = []
    for expected_entry in expected_entries:
        if isinstance(expected_entry, _BaseEntry):
            if expected_entry.is_compatible_with_current_python_version():
                filtered_expected_entries.append(expected_entry)
        else:
            filtered_expected_entries.append(expected_entry)

    expected_entries_count = len(filtered_expected_entries)
    any_mismatch = False
    result = ''
    template = u'\n{line!s:%s}   {expected_entry}  {arrow}' % max(map(len, lines))
    for expected_entry, line in zip_longest(filtered_expected_entries, lines, fillvalue=""):
        mismatch = not (expected_entry and expected_entry.check(line))
        any_mismatch |= mismatch
        arrow = '<===' * mismatch
        result += template.format(**locals())

    if len(lines) != expected_entries_count:
        result += '\nOutput has {} lines, while we expect {} lines.'.format(
                len(lines), len(expected_entries))

    if any_mismatch:
        raise OutputFailure(result)


def assert_sample_output(module):
    with mini_toolbox.OutputCapturer(stdout=False,
                                     stderr=True) as output_capturer:
        module.main()

    placeholder_time = '00:00:00.000000'
    time_pattern = '[0-9:.]{15}'

    def normalise(out):
        out = re.sub(time_pattern, placeholder_time, out).strip()
        out = re.sub(
            r'^( *)Source path:\.\.\. .*$',
            r'\1Source path:... Whatever',
            out,
            flags=re.MULTILINE
        )
        return out


    output = output_capturer.string_io.getvalue()

    try:
        assert (
                normalise(output) ==
                normalise(module.expected_output)
        )
    except AssertionError:
        print('\n\nActual Output:\n\n' + output)  # to copy paste into expected_output
        raise  # show pytest diff (may need -vv flag to see in full)


