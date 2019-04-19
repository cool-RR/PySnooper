# Copyright 2019 Ram Rachum.
# This program is distributed under the MIT license.

import io
import re
import abc

from python_toolbox import caching
from python_toolbox import sys_tools

import pysnooper


class Entry(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def check(self, s: str) -> bool:
        pass

class VariableEntry(Entry):
    line_pattern = re.compile(
        r"""^            ==> (?P<name>[^ ]*) = (?P<value>.*)$"""
    )
    def __init__(self, name=None, value=None, *,
                 name_regex=None, value_regex=None):
        if name is not None:
            assert name_regex is None
        if value is not None:
            assert value_regex is None
            
        self.name = name
        self.value = value
        self.name_regex = (None if name_regex is None else
                                                        re.compile(name_regex))
        self.value_regex = (None if value_regex is None else
                                                       re.compile(value_regex))
        
    def _check_name(self, name: str) -> bool:
        if self.name is not None:
            return name == self.name
        elif self.name_regex is not None:
            return self.name_regex.fullmatch(name)
        else:
            return True
        
    def _check_value(self, value: str) -> bool:
        if self.value is not None:
            return value == self.value
        elif self.value_regex is not None:
            return self.value_regex.fullmatch(value)
        else:
            return True
            
    def check(self, s: str) -> bool:
        match: re.Match = self.line_pattern.fullmatch(s)
        if not match:
            return False
        name, value = match.groups()
        return self._check_name(name) and self._check_value(value)
        

class EventEntry(Entry):
    def __init__(self, source=None, *, source_regex=None):
        if source is not None:
            assert source_regex is None
            
        self.source = source
        self.source_regex = (None if source_regex is None else
                                                      re.compile(source_regex))

    line_pattern = re.compile(
        (r"""^[0-9:.]{15} (?P<event_name>[a-z]*) +"""
         r"""(?P<line_number>[0-9]*) +(?P<source>.*)$""")
    )
    
    @caching.CachedProperty
    def event_name(self):
        return re.match('^[A-Z][a-z]*', type(self).__name__).group(0).lower()
    
    def _check_source(self, source: str) -> bool:
        if self.source is not None:
            return source == self.source
        elif self.source_regex is not None:
            return self.source_regex.fullmatch(source)
        else:
            return True
            
    def check(self, s: str) -> bool:
        match: re.Match = self.line_pattern.fullmatch(s)
        if not match:
            return False
        event_name, _, source = match.groups()
        return event_name == self.event_name and self._check_source(source)
        


class CallEntry(EventEntry):
    pass
        
class LineEntry(EventEntry):
    pass
        
class ReturnEntry(EventEntry):
    pass
        
class ExceptionEntry(EventEntry):
    pass
        
class OpcodeEntry(EventEntry):
    pass
        
        
def check_output(output, expected_entries):
    lines = tuple(filter(None, output.split('\n')))
    if len(lines) != len(expected_entries):
        return False
    return all(expected_entry.check(line) for
               expected_entry, line in zip(expected_entries, lines))
    

def test_pysnooper():
    string_io = io.StringIO()
    @pysnooper.snoop(string_io)
    def my_function(foo):
        x = 7
        y = 8
        return y + x
    result = my_function('baba')
    assert result == 15
    output = string_io.getvalue()
    assert check_output(
        output,
        (
            VariableEntry('foo', "'baba'"),
            CallEntry(),
            LineEntry('x = 7'), 
            VariableEntry('x', '7'), 
            LineEntry('y = 8'), 
            VariableEntry('y', '8'), 
            LineEntry('return y + x'), 
            ReturnEntry('return y + x'), 
        )
    )
    
def test_variables():

    class Foo:
        def __init__(self):
            self.x = 2
            
        def square(self):
            self.x **= 2

    @pysnooper.snoop(variables=('foo.x', 're'))
    def my_function():
        foo = Foo()
        for i in range(2):
            foo.square()

    with sys_tools.OutputCapturer(stdout=False,
                                  stderr=True) as output_capturer:
        result = my_function()
    assert result is None
    output = output_capturer.string_io.getvalue()
    assert check_output(
        output,
        (
            VariableEntry('Foo'),
            VariableEntry('re'),
            CallEntry(),
            LineEntry('foo = Foo()'), 
            VariableEntry('foo'),
            VariableEntry('foo.x', '2'),
            LineEntry(), 
            VariableEntry('i', '0'),
            LineEntry(), 
            VariableEntry('foo.x', '4'),
            LineEntry(), 
            VariableEntry('i', '1'),
            LineEntry(), 
            VariableEntry('foo.x', '16'),
            LineEntry(), 
            ReturnEntry(), 
        )
    )