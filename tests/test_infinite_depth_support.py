# -*- coding: utf-8 -*-
# Copyright 2023 Elijah Qi and Liuqing Yang.
# This program is distributed under the MIT license.

import io
import textwrap
import threading
import types
import sys

from pysnooper.utils import truncate
import pytest

import pysnooper
from pysnooper import pycompat
from pysnooper.variables import needs_parentheses
from .utils import (assert_output, assert_sample_output, VariableEntry,
                    CallEntry, LineEntry, ReturnEntry, OpcodeEntry,
                    ReturnValueEntry, ExceptionEntry, ExceptionValueEntry,
                    SourcePathEntry, CallEndedByExceptionEntry,
                    ElapsedTimeEntry)
from . import mini_toolbox

@pytest.mark.parametrize("normalize", (True, False))
def test_var_order(normalize):
    string_io = io.StringIO()

    def func1(x):
        return x

    def func(x):
        func1(x)

    def foo(x):
        func(x)

    def recursive_function(x):
        if x == 0:
            return 1
        
        foo(x)

        recursive_function(x - 1)

    with pysnooper.snoop(string_io, depth=float('inf'), normalize=normalize, color=False):
        recursive_function(1)

    output = string_io.getvalue()
    with open('test_var_order.txt', 'w') as f:
        f.write(output)
    
    assert_output(
        output,
        (
        SourcePathEntry(),
        VariableEntry(),
        VariableEntry(),
        VariableEntry(),
        VariableEntry(),
        VariableEntry(),
        VariableEntry(),
        LineEntry("recursive_function(1)"),
        VariableEntry("x", "1"),
        VariableEntry("foo"),
        VariableEntry("recursive_function"),

        CallEntry("def recursive_function(x):"),
        LineEntry("if x == 0:"),
        LineEntry(),
        LineEntry("foo(x)"),

        VariableEntry("x", "1"),
        VariableEntry("func1"),
        CallEntry("def func(x):"),
        LineEntry("func1(x)"),

        VariableEntry("x", "1"),
        VariableEntry("func1"),
        CallEntry("def func(x):"),
        LineEntry("func1(x)"),

        VariableEntry("x", "1"),
        CallEntry("def func1(x):"),
        LineEntry("return x"),
        ReturnEntry(),
        ReturnValueEntry("1"),

        ReturnEntry(),
        ReturnValueEntry("None"),

        ReturnEntry(),
        ReturnValueEntry("None"),

        LineEntry("recursive_function(x - 1)"),

        VariableEntry("x", "0"),
        VariableEntry("foo"),
        VariableEntry("recursive_function"),

        CallEntry("def recursive_function(x):"),
        LineEntry("if x == 0:"),
        LineEntry("return 1"),
        ReturnEntry(),
        ReturnValueEntry("1"),

        ReturnEntry(),
        ReturnValueEntry("None"),

        LineEntry("with pysnooper.snoop(string_io, depth=float('inf'), normalize=normalize, color=False):"),
        ElapsedTimeEntry(),
        ),
        normalize=normalize,
    )
