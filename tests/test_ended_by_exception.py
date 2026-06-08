"""Tests for call_ended_by_exception, the 'return'-via-exception detector.

Regression test for https://github.com/cool-RR/PySnooper/issues/260: a frame's
f_lasti can be -1, and co_code[-1] would read the wrong opcode and misreport a
normal return as "Call ended by exception".
"""

import io
import opcode
from unittest.mock import Mock

import pysnooper
from pysnooper.tracer import call_ended_by_exception


def _frame(co_code, f_lasti):
    frame = Mock()
    frame.f_lasti = f_lasti
    frame.f_code.co_code = co_code
    return frame


def test_negative_f_lasti_is_not_an_exception():
    # Last byte is a non-return opcode, so reading co_code[-1] (the old bug)
    # would misreport an exception. With f_lasti == -1 it must be a normal
    # return.
    co_code = bytes([0, opcode.opmap["NOP"]])
    assert call_ended_by_exception(_frame(co_code, -1), "return", None) is False


def test_last_opcode_return_is_normal_return():
    co_code = bytes([opcode.opmap["RETURN_VALUE"], 0])
    assert call_ended_by_exception(_frame(co_code, 0), "return", None) is False


def test_last_opcode_not_return_is_exception():
    co_code = bytes([opcode.opmap["NOP"], 0])
    assert call_ended_by_exception(_frame(co_code, 0), "return", None) is True


def test_non_return_event_is_never_exception():
    co_code = bytes([opcode.opmap["NOP"], 0])
    assert call_ended_by_exception(_frame(co_code, 0), "call", None) is False


def test_unstarted_generator_close_is_not_an_exception():
    string_io = io.StringIO()

    def gen(n):
        for i in range(n):
            yield i

    @pysnooper.snoop(string_io, depth=2, color=False)
    def main():
        g = gen(5)
        g.close()
        return 42

    assert main() == 42
    output = string_io.getvalue()
    assert "Call ended by exception" not in output
    assert "Return value:.. 42" in output
