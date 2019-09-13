# Copyright 2019 Ram Rachum and collaborators.
# This program is distributed under the MIT license.

import io
import textwrap
import threading
import collections
import types
import os
import sys

from pysnooper.utils import truncate
import pytest

import pysnooper
from pysnooper.variables import needs_parentheses
from pysnooper import pycompat
from .utils import (assert_output, assert_sample_output, VariableEntry,
                    CallEntry, LineEntry, ReturnEntry, OpcodeEntry,
                    ReturnValueEntry, ExceptionEntry, SourcePathEntry)
from . import mini_toolbox


def test_rejecting_coroutine_functions():
    if sys.version_info[:2] <= (3, 4):
        pytest.skip()

    class Thing:
        pass

    thing = Thing()

    code = textwrap.dedent('''
    async def foo(x):
        return 'lol'
    thing.foo = foo
    ''')
    exec(code)
    foo = thing.foo

    assert pycompat.iscoroutinefunction(foo)
    assert not pycompat.isasyncgenfunction(foo)
    with pytest.raises(NotImplementedError):
        pysnooper.snoop()(foo)


def test_rejecting_async_generator_functions():
    if sys.version_info[:2] <= (3, 6):
        pytest.skip()

    class Thing:
        pass

    thing = Thing()

    code = textwrap.dedent('''
    async def foo(x):
        yield 'lol'
    thing.foo = foo
    ''')
    exec(code)
    foo = thing.foo

    assert not pycompat.iscoroutinefunction(foo)
    assert pycompat.isasyncgenfunction(foo)
    with pytest.raises(NotImplementedError):
        pysnooper.snoop()(foo)


