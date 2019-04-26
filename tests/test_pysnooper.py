# Copyright 2019 Ram Rachum and collaborators.
# This program is distributed under the MIT license.

import io
import textwrap

from python_toolbox import sys_tools
from python_toolbox import temp_file_tools
from pysnooper.third_party import six
import pytest

import pysnooper
from pysnooper.third_party import six
from .utils import (assert_output, VariableEntry, CallEntry, LineEntry,
                    ReturnEntry, OpcodeEntry, ReturnValueEntry, ExceptionEntry)


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
            CallEntry('def my_function(foo):'),
            LineEntry('x = 7'),
            VariableEntry('x', '7'),
            LineEntry('y = 8'),
            VariableEntry('y', '8'),
            LineEntry('return y + x'),
            ReturnEntry('return y + x'),
            ReturnValueEntry('15'),
        )
    )


def test_variables():

    class Foo(object):
        def __init__(self):
            self.x = 2

        def square(self):
            self.x **= 2

    @pysnooper.snoop(variables=('foo.x', 'io'))
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
            CallEntry('def my_function():'),
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
            ReturnValueEntry('None')
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
            CallEntry('def f1(x1):'),
            LineEntry(),

            VariableEntry(),
            VariableEntry(),
            CallEntry('def f2(x2):'),
            LineEntry(),

            VariableEntry(),
            VariableEntry(),
            CallEntry('def f3(x3):'),
            LineEntry(),

            VariableEntry(),
            LineEntry(),
            ReturnEntry(),
            ReturnValueEntry('20'),

            VariableEntry(),
            LineEntry(),
            ReturnEntry(),
            ReturnValueEntry('20'),

            VariableEntry(),
            LineEntry(),
            ReturnEntry(),
            ReturnValueEntry('20'),
        )
    )


def test_method_and_prefix():
    class Baz(object):
        def __init__(self):
            self.x = 2

        @pysnooper.snoop(variables=('self.x',), prefix='ZZZ')
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
            VariableEntry('self', prefix='ZZZ'),
            VariableEntry('self.x', '2', prefix='ZZZ'),
            CallEntry('def square(self):', prefix='ZZZ'),
            LineEntry('foo = 7', prefix='ZZZ'),
            VariableEntry('foo', '7', prefix='ZZZ'),
            LineEntry('self.x **= 2', prefix='ZZZ'),
            VariableEntry('self.x', '4', prefix='ZZZ'),
            LineEntry(prefix='ZZZ'),
            ReturnEntry(prefix='ZZZ'),
            ReturnValueEntry(prefix='ZZZ'),
        ),
        prefix='ZZZ'
    )


def test_file_output():
    with temp_file_tools.create_temp_folder(prefix='pysnooper') as folder:
        path = folder / 'foo.log'

        @pysnooper.snoop(str(path))
        def my_function(_foo):
            x = 7
            y = 8
            return y + x

        result = my_function('baba')
        assert result == 15
        with path.open() as output_file:
            output = output_file.read()
        assert_output(
            output,
            (
                VariableEntry('_foo', value_regex="u?'baba'"),
                CallEntry('def my_function(_foo):'),
                LineEntry('x = 7'),
                VariableEntry('x', '7'),
                LineEntry('y = 8'),
                VariableEntry('y', '8'),
                LineEntry('return y + x'),
                ReturnEntry('return y + x'),
                ReturnValueEntry('15'),
            )
        )


def test_confusing_decorator_lines():
    string_io = io.StringIO()

    def empty_decorator(function):
        return function

    @empty_decorator
    @pysnooper.snoop(string_io,
                     depth=2)  # Multi-line decorator for extra confusion!
    @empty_decorator
    @empty_decorator
    def my_function(foo):
        x = lambda bar: 7
        y = 8
        return y + x(foo)

    result = my_function('baba')
    assert result == 15
    output = string_io.getvalue()
    assert_output(
        output,
        (
            VariableEntry('foo', value_regex="u?'baba'"),
            CallEntry('def my_function(foo):'),
            LineEntry(),
            VariableEntry(),
            LineEntry(),
            VariableEntry(),
            LineEntry(),
            # inside lambda
            VariableEntry('bar', value_regex="u?'baba'"),
            CallEntry('x = lambda bar: 7'),
            LineEntry(),
            ReturnEntry(),
            ReturnValueEntry('7'),
            # back in my_function
            ReturnEntry(),
            ReturnValueEntry('15'),
        )
    )


def test_lambda():
    string_io = io.StringIO()
    my_function = pysnooper.snoop(string_io)(lambda x: x ** 2)
    result = my_function(7)
    assert result == 49
    output = string_io.getvalue()
    assert_output(
        output,
        (
            VariableEntry('x', '7'),
            CallEntry(source_regex='^my_function = pysnooper.*'),
            LineEntry(source_regex='^my_function = pysnooper.*'),
            ReturnEntry(source_regex='^my_function = pysnooper.*'),
            ReturnValueEntry('49'),
        )
    )


def test_unavailable_source():
    with temp_file_tools.create_temp_folder(prefix='pysnooper') as folder, \
            sys_tools.TempSysPathAdder(str(folder)):
        module_name = 'iaerojajsijf'
        python_file_path = folder / ('%s.py' % (module_name,))
        content = textwrap.dedent(u'''
            import pysnooper
            @pysnooper.snoop()
            def f(x):
                return x
        ''')
        with python_file_path.open('w') as python_file:
            python_file.write(content)
        module = __import__(module_name)
        python_file_path.unlink()
        with sys_tools.OutputCapturer(stdout=False,
                                      stderr=True) as output_capturer:
            result = getattr(module, 'f')(7)
        assert result == 7
        output = output_capturer.output
        assert_output(
            output,
            (
                VariableEntry(stage='starting'),
                CallEntry('SOURCE IS UNAVAILABLE'),
                LineEntry('SOURCE IS UNAVAILABLE'),
                ReturnEntry('SOURCE IS UNAVAILABLE'),
                ReturnValueEntry('7'),
            )
        )


def test_no_overwrite_by_default():
    with temp_file_tools.create_temp_folder(prefix='pysnooper') as folder:
        path = folder / 'foo.log'
        with path.open('w') as output_file:
            output_file.write(u'lala')
        @pysnooper.snoop(str(path))
        def my_function(foo):
            x = 7
            y = 8
            return y + x
        result = my_function('baba')
        assert result == 15
        with path.open() as output_file:
            output = output_file.read()
        assert output.startswith('lala')
        shortened_output = output[4:]
        assert_output(
            shortened_output,
            (
                VariableEntry('foo', value_regex="u?'baba'"),
                CallEntry('def my_function(foo):'),
                LineEntry('x = 7'),
                VariableEntry('x', '7'),
                LineEntry('y = 8'),
                VariableEntry('y', '8'),
                LineEntry('return y + x'),
                ReturnEntry('return y + x'),
                ReturnValueEntry('15'),
            )
        )


def test_overwrite():
    with temp_file_tools.create_temp_folder(prefix='pysnooper') as folder:
        path = folder / 'foo.log'
        with path.open('w') as output_file:
            output_file.write(u'lala')
        @pysnooper.snoop(str(path), overwrite=True)
        def my_function(foo):
            x = 7
            y = 8
            return y + x
        result = my_function('baba')
        result = my_function('baba')
        assert result == 15
        with path.open() as output_file:
            output = output_file.read()
        assert 'lala' not in output
        assert_output(
            output,
            (
                VariableEntry('foo', value_regex="u?'baba'"),
                CallEntry('def my_function(foo):'),
                LineEntry('x = 7'),
                VariableEntry('x', '7'),
                LineEntry('y = 8'),
                VariableEntry('y', '8'),
                LineEntry('return y + x'),
                ReturnEntry('return y + x'),
                ReturnValueEntry('15'),

                VariableEntry('foo', value_regex="u?'baba'"),
                CallEntry('def my_function(foo):'),
                LineEntry('x = 7'),
                VariableEntry('x', '7'),
                LineEntry('y = 8'),
                VariableEntry('y', '8'),
                LineEntry('return y + x'),
                ReturnEntry('return y + x'),
                ReturnValueEntry('15'),
            )
        )


def test_error_in_overwrite_argument():
    with temp_file_tools.create_temp_folder(prefix='pysnooper') as folder:
        with pytest.raises(Exception, match='can only be used when writing'):
            @pysnooper.snoop(overwrite=True)
            def my_function(foo):
                x = 7
                y = 8
                return y + x

