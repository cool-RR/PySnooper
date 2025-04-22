# -*- coding: utf-8 -*-
# Copyright 2023 Elijah Qi and Liuqing Yang.
# This program is distributed under the MIT license.

import io
import textwrap
import threading
import types
import os
import sys

from pysnooper.utils import truncate
import pytest

import pysnooper
from pysnooper.variables import needs_parentheses
from ..utils import (assert_output, assert_sample_output, VariableEntry,
                    CallEntry, LineEntry, ReturnEntry, OpcodeEntry,
                    ReturnValueEntry, ExceptionEntry, ExceptionValueEntry,
                    SourcePathEntry, CallEndedByExceptionEntry,
                    ElapsedTimeEntry)
from .. import mini_toolbox
from . import factorial


def test_multiple_files():
    with mini_toolbox.OutputCapturer(stdout=False,
                                     stderr=True) as output_capturer:
        result = factorial.factorial(3)
    assert result == 6
    output = output_capturer.string_io.getvalue()
    assert_output(
        output,
        (
            SourcePathEntry(source_path_regex=r'.*factorial\.py$'),
            VariableEntry('x', '3'),
            CallEntry(),
            LineEntry(),
            LineEntry(),
            VariableEntry('x', '2'),
            CallEntry(),
            LineEntry(),
            LineEntry(),
            VariableEntry('x', '1'),
            CallEntry(),
            LineEntry(),
            LineEntry(),
            ReturnEntry(),
            ReturnValueEntry('1'),
            ElapsedTimeEntry(),
            ReturnEntry(),
            ReturnValueEntry('2'),
            ElapsedTimeEntry(),
            ReturnEntry(),
            ReturnValueEntry('6'),
            ElapsedTimeEntry()
        )
    )


