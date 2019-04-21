# Copyright 2019 Ram Rachum.
# This program is distributed under the MIT license.

import re
import abc

from python_toolbox import caching

import pysnooper.pycompat


class _BaseEntry(pysnooper.pycompat.ABC):
    @abc.abstractmethod
    def check(self, s: str) -> bool:
        pass
    
class VariableEntry(_BaseEntry):
    line_pattern = re.compile(
        r"""^(?P<indent>(?: {4})*)(?P<stage>New|Modified|Starting) var:"""
        r"""\.{2,7} (?P<name>[^ ]+) = (?P<value>.+)$"""
    )
    def __init__(self, name=None, value=None, stage=None, *,
                 name_regex=None, value_regex=None):
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

    def _check_name(self, name: str) -> bool:
        if self.name is not None:
            return name == self.name
        elif self.name_regex is not None:
            return self.name_regex.match(name)
        else:
            return True

    def _check_value(self, value: str) -> bool:
        if self.value is not None:
            return value == self.value
        elif self.value_regex is not None:
            return self.value_regex.match(value)
        else:
            return True

    def _check_stage(self, stage: str) -> bool:
        stage = stage.lower()
        if self.stage is None:
            return stage in ('starting', 'new', 'modified')
        else:
            return stage == self.value

    def check(self, s: str) -> bool:
        match = self.line_pattern.match(s)
        if not match:
            return False
        indent, stage, name, value = match.groups()
        return (self._check_name(name) and self._check_value(value) and
                self._check_stage(stage))


class _BaseEventEntry(_BaseEntry):
    def __init__(self, source=None, *, source_regex=None):
        if type(self) is _BaseEventEntry:
            raise TypeError
        if source is not None:
            assert source_regex is None

        self.source = source
        self.source_regex = (None if source_regex is None else
                             re.compile(source_regex))

    line_pattern = re.compile(
        (r"""^(?P<indent>(?: {4})*)[0-9:.]{15} (?P<event_name>[a-z]*) +"""
         r"""(?P<line_number>[0-9]*) +(?P<source>.*)$""")
    )

    @caching.CachedProperty
    def event_name(self):
        return re.match('^[A-Z][a-z]*', type(self).__name__).group(0).lower()

    def _check_source(self, source: str) -> bool:
        if self.source is not None:
            return source == self.source
        elif self.source_regex is not None:
            return self.source_regex.match(source)
        else:
            return True

    def check(self, s: str) -> bool:
        match = self.line_pattern.match(s)
        if not match:
            return False
        indent, event_name, _, source = match.groups()
        return event_name == self.event_name and self._check_source(source)



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
        

def assert_output(output, expected_entries):
    lines = tuple(filter(None, output.split('\n')))
    if len(lines) != len(expected_entries):
        raise OutputFailure(
            'Output has {len(lines)} lines, while we expect '
            '{len(expected_entries)} lines.'.format(**locals())
        )
    for expected_entry, line in zip(expected_entries, lines):
        if not expected_entry.check(line):
            raise OutputFailure(line)


