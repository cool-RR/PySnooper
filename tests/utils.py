# Copyright 2019 Ram Rachum and collaborators.
# This program is distributed under the MIT license.

import re
import abc
import inspect

from python_toolbox import caching

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
    def __init__(self, prefix=''):
        self.prefix = prefix

    @abc.abstractmethod
    def check(self, s):
        pass

class _BaseValueEntry(_BaseEntry):
    def __init__(self, prefix=''):
        _BaseEntry.__init__(self, prefix=prefix)
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



class VariableEntry(_BaseValueEntry):
    def __init__(self, name=None, value=None, stage=None, prefix='',
                 name_regex=None, value_regex=None, ):
        _BaseValueEntry.__init__(self, prefix=prefix)
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
        r"""^(?P<name>[^ ]+) = (?P<value>.+)$"""
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

class ReturnValueEntry(_BaseValueEntry):
    def __init__(self, value=None, value_regex=None, prefix=''):
        _BaseValueEntry.__init__(self, prefix=prefix)
        if value is not None:
            assert value_regex is None

        self.value = value
        self.value_regex = (None if value_regex is None else
                            re.compile(value_regex))

    _preamble_pattern = re.compile(
        r"""^Return value$"""
    )

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

class _BaseEventEntry(_BaseEntry):
    def __init__(self, source=None, source_regex=None, prefix=''):
        _BaseEntry.__init__(self, prefix=prefix)
        if type(self) is _BaseEventEntry:
            raise TypeError
        if source is not None:
            assert source_regex is None
        self.line_pattern = re.compile(
            r"""^%s(?P<indent>(?: {4})*)[0-9:.]{15} """
            r"""(?P<event_name>[a-z_]*) +(?P<line_number>[0-9]*) """
            r"""+(?P<source>.*)$""" % (re.escape(self.prefix,))
        )

        self.source = source
        self.source_regex = (None if source_regex is None else
                             re.compile(source_regex))


    @caching.CachedProperty
    def event_name(self):
        return re.match('^[A-Z][a-z_]*', type(self).__name__).group(0).lower()

    def _check_source(self, source):
        if self.source is not None:
            return source == self.source
        elif self.source_regex is not None:
            return self.source_regex.match(source)
        else:
            return True

    def check(self, s):
        match = self.line_pattern.match(s)
        if not match:
            return False
        _, event_name, _, source = match.groups()
        return (event_name == self.event_name and
                self._check_source(source))



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


def assert_output(output, expected_entries, prefix=None):
    lines = tuple(filter(None, output.split('\n')))
    if len(lines) != len(expected_entries):
        raise OutputFailure(
            'Output has {len(lines)} lines, while we expect '
            '{len(expected_entries)} lines.'.format(**locals())
        )
    if prefix is not None:
        for line in lines:
            if not line.startswith(prefix):
                raise OutputFailure(line)

    for expected_entry, line in zip(expected_entries, lines):
        if not expected_entry.check(line):
            raise OutputFailure(line)


