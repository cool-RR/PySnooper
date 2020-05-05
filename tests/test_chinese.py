# -*- coding: utf-8 -*-
# Copyright 2019 Ram Rachum and collaborators.
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



def test_chinese():
    with mini_toolbox.create_temp_folder(prefix='pysnooper') as folder:
        path = folder / 'foo.log'
        @pysnooper.snoop(path)
        def foo():
            a = 1
            x = '失败'
            return 7

        foo()
        with path.open(encoding='utf-8') as file:
            output = file.read()
        assert_output(
            output,
            (
                SourcePathEntry(),
                CallEntry(),
                LineEntry(),
                VariableEntry('a'),
                LineEntry(u"x = '失败'"),
                VariableEntry(u'x', (u"'失败'" if pycompat.PY3 else None)),
                LineEntry(),
                ReturnEntry(),
                ReturnValueEntry('7'),
                ElapsedTimeEntry(),
            ),
        )
