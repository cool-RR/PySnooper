# Copyright 2019 Ram Rachum.
# This program is distributed under the MIT license.

import io
import re
import abc

from python_toolbox import caching
from python_toolbox import sys_tools

import pysnooper

from .utils import (assert_output, VariableEntry, CallEntry, LineEntry,
                    ReturnEntry, OpcodeEntry, ExceptionEntry)


def test_string_io():
    string_io = io.StringIO()
    @pysnooper.snoop(string_io)
    def my_function(foo):
        x = 7
        y = 8
        return y + x
    result = my_function('baba')
    assert result == 15
    output = string_io.getvalue()
    assert_output(
        output,
        (
            VariableEntry('foo', value_regex="u?'baba'"),
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

    class Foo(object):
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
    assert_output(
        output,
        (
            VariableEntry(),
            VariableEntry(),
            CallEntry(),
            LineEntry('foo = Foo()'),
            VariableEntry(),
            VariableEntry(),
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

def test_depth():
    string_io = io.StringIO()

    def f4(x4):
        result4 = x4 * 2
        return result4

    def f3(x3):
        result3 = f4(x3)
        return result3

    def f2(x2):
        result2 = f3(x2)
        return result2

    @pysnooper.snoop(string_io, depth=3)
    def f1(x1):
        result1 = f2(x1)
        return result1

    result = f1(10)
    assert result == 20
    output = string_io.getvalue()
    assert_output(
        output,
        (
            VariableEntry(),
            VariableEntry(),
            CallEntry(),
            LineEntry(),

            VariableEntry(),
            VariableEntry(),
            CallEntry(),
            LineEntry(),

            VariableEntry(),
            VariableEntry(),
            CallEntry(),
            LineEntry(),

            VariableEntry(),
            LineEntry(),
            ReturnEntry(),

            VariableEntry(),
            LineEntry(),
            ReturnEntry(),

            VariableEntry(),
            LineEntry(),
            ReturnEntry(),
        )
    )


def test_method_and_prefix():

    class Baz(object):
        def __init__(self):
            self.x = 2

        @pysnooper.snoop(variables=('self.x'), prefix='ZZZ')
        def square(self):
            foo = 7
            self.x **= 2
            return self

    baz = Baz()

    with sys_tools.OutputCapturer(stdout=False,
                                  stderr=True) as output_capturer:
        result = baz.square()
    assert result is baz
    assert result.x == 4
    output = output_capturer.string_io.getvalue()
    assert_output(
        output,
        (
            VariableEntry(),
            CallEntry(),
            LineEntry('foo = 7'),
            VariableEntry('foo', '7'),
            LineEntry('self.x **= 2'),
            LineEntry(),
            ReturnEntry(),
        ),
        prefix='ZZZ'
    )
