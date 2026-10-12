import io
import sys

import pytest

import pysnooper


@pytest.mark.parametrize('existing_trace', [False, True])
@pytest.mark.parametrize('raise_error', [False, True])
def test_context_restores_local_trace(existing_trace, raise_error):
    events = []

    def local_trace(frame, event, arg):
        events.append(event)
        return local_trace

    def global_trace(frame, event, arg):
        return local_trace

    frame = sys._getframe()
    previous_global = sys.gettrace()
    previous_local = frame.f_trace
    expected_local = local_trace if existing_trace else None
    expected_global = global_trace if existing_trace else None
    try:
        sys.settrace(expected_global)
        frame.f_trace = expected_local
        try:
            with pysnooper.snoop(io.StringIO(), color=False):
                if raise_error:
                    raise ValueError('test')
        except ValueError:
            pass
        assert sys.gettrace() is expected_global
        assert frame.f_trace is expected_local
        events[:] = []
        marker = True
        assert marker
        assert ('line' in events) is existing_trace
    finally:
        sys.settrace(previous_global)
        frame.f_trace = previous_local
