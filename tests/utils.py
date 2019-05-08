# Copyright 2019 Ram Rachum and collaborators.
# This program is distributed under the MIT license.

import abc
import re

import pysnooper.pycompat
from pysnooper import formatting
from pysnooper.formatting import DefaultFormatter
from pysnooper.third_party.six.moves import zip_longest
from pysnooper.tracer import Tracer
from pysnooper.utils import get_shortish_repr
from python_toolbox import caching


class CollectingFormatter(object):
    def __init__(self, *_, **__):
        self.entries = []

    def format(self, event):
        self.entries.extend(event.entries)
        for entry in self.entries:
            if isinstance(entry, formatting.ReturnValueEntry):
                entry.value_repr = get_shortish_repr(entry.value)
        return ''


class CollectingTracer(Tracer):
    formatter_class = CollectingFormatter


class NoTimeFormatter(DefaultFormatter):
    datetime_format = 'insert_the_time_here'


class NoTimeTracer(Tracer):
    formatter_class = NoTimeFormatter


class _BaseEntry(pysnooper.pycompat.ABC):
    @abc.abstractmethod
    def check(self, s):
        pass

    def __repr__(self):
        items = []
        for key, value in self.__dict__.items():
            suffix = '_checker'
            if key.endswith(suffix):
                key = key[:-len(suffix)]
                if value.blank():
                    continue
            else:
                if value is None:
                    continue

            items.append('{}={!r}'.format(key, value))

        return '{}({})'.format(
            self.__class__.__name__,
            ', '.join(items),
        )


class PartChecker(object):
    def __init__(self, value, regex):
        assert (value is None) or (regex is None)
        self.value = value
        self.regex = regex

    def check(self, value):
        if self.value is not None:
            return value == self.value
        elif self.regex is not None:
            return re.match(self.regex, value)
        else:
            return True

    def blank(self):
        return self.value is None and self.regex is None
    
    def __repr__(self):
        if self.value is not None:
            return repr(self.value)
        elif self.regex is not None:
            return 're({})'.format(repr(self.value))
        else:
            return '*'

class _BaseValueEntry(_BaseEntry):
    def __init__(self, value=None, value_regex=None):
        self.value_checker = PartChecker(value, value_regex)

    def check(self, other):
        return self.__class__.__name__ == other.__class__.__name__ and \
               self.value_checker.check(other.value_repr)


class VariableEntry(_BaseValueEntry):
    def __init__(self, name=None, value=None, stage=None, name_regex=None, value_regex=None):
        _BaseValueEntry.__init__(self, value, value_regex)
        assert stage in (None, 'starting', 'new', 'modified')
        self.name_checker = PartChecker(name, name_regex)
        self.stage = stage

    def check(self, other):
        return (
                _BaseValueEntry.check(self, other)
                and self.name_checker.check(other.name)
                and self._check_stage(other.type)
        )

    def _check_stage(self, stage):
        stage = stage.lower()
        if self.stage is None:
            return stage in ('starting', 'new', 'modified')
        else:
            return stage == self.stage


class ReturnValueEntry(_BaseValueEntry):
    pass


class _BaseEventEntry(_BaseEntry):
    def __init__(self, source=None, source_regex=None):
        _BaseEntry.__init__(self)
        if type(self) is _BaseEventEntry:
            raise TypeError
        self.source_checker = PartChecker(source, source_regex)

    @caching.CachedProperty
    def event_name(self):
        return re.match('^[A-Z][a-z_]*', type(self).__name__).group(0).lower()

    def check(self, other):
        return (getattr(other, 'event', '') == self.event_name
                and self.source_checker.check(other.source_line.strip()))


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


def assert_output(tracer, expected_entries):
    entries = tracer.formatter.entries
    formatter = DefaultFormatter('')
    lines = [formatter.format_entry(entry, None) for entry in entries]
    any_mismatch = False
    result = ''
    template = '\n{line!s:%s}   {expected_entry}  {arrow}' % max(map(len, lines))
    for expected_entry, entry, line in zip_longest(expected_entries, entries, lines, fillvalue=""):
        mismatch = not (expected_entry and entry and expected_entry.check(entry))
        any_mismatch |= mismatch
        arrow = '<===' * mismatch
        result += template.format(**locals())

    if len(lines) != len(expected_entries):
        result += '\nOutput has {} lines, while we expect {} lines.'.format(
                len(lines), len(expected_entries))

    if any_mismatch:
        raise OutputFailure(result)
