import io
import sys

import pytest

import pysnooper


@pytest.mark.parametrize('exception_type', (
    ValueError, KeyboardInterrupt, SystemExit, GeneratorExit,
))
def test_generator_throw_reaches_handler(exception_type):
    original_trace = sys.gettrace()
    output = io.StringIO()

    @pysnooper.snoop(output, color=False)
    def generator():
        try:
            yield 'ready'
        except BaseException as error:
            assert sys.gettrace() is not original_trace
            yield error
        yield 'done'

    iterator = generator()
    error = exception_type('injected')
    try:
        assert next(iterator) == 'ready'
        try:
            result = iterator.throw(error)
        except BaseException as propagated:
            pytest.fail('Exception did not reach handler: {!r}'.format(
                propagated))
        assert result is error
        assert sys.gettrace() is original_trace
        assert next(iterator) == 'done'
        with pytest.raises(StopIteration):
            next(iterator)
    finally:
        iterator.close()
    assert sys.gettrace() is original_trace


@pytest.mark.parametrize('exception_type', (KeyboardInterrupt, SystemExit))
def test_generator_throw_unhandled_exception(exception_type):
    original_trace = sys.gettrace()

    @pysnooper.snoop(io.StringIO(), color=False)
    def generator():
        yield 'ready'

    iterator = generator()
    assert next(iterator) == 'ready'
    error = exception_type('unhandled')
    with pytest.raises(exception_type) as exc_info:
        iterator.throw(error)
    assert exc_info.value is error
    assert sys.gettrace() is original_trace


def test_generator_close_traces_cleanup():
    original_trace = sys.gettrace()
    output = io.StringIO()
    cleanup_traced = []

    @pysnooper.snoop(output, color=False)
    def generator():
        try:
            yield 'ready'
        finally:
            cleanup_traced.append(sys.gettrace() is not original_trace)

    iterator = generator()
    assert next(iterator) == 'ready'
    iterator.close()
    assert cleanup_traced == [True]
    assert 'cleanup_traced.append' in output.getvalue()
    assert sys.gettrace() is original_trace


def test_generator_close_propagates_cleanup_exception():
    original_trace = sys.gettrace()
    error = ValueError('cleanup failed')

    @pysnooper.snoop(io.StringIO(), color=False)
    def generator():
        try:
            yield 'ready'
        finally:
            raise error

    iterator = generator()
    assert next(iterator) == 'ready'
    with pytest.raises(ValueError) as exc_info:
        iterator.close()
    assert exc_info.value is error
    assert sys.gettrace() is original_trace


def test_generator_close_rejects_yield_after_exit():
    original_trace = sys.gettrace()

    @pysnooper.snoop(io.StringIO(), color=False)
    def generator():
        try:
            yield 'ready'
        except GeneratorExit:
            yield 'ignored close'

    iterator = generator()
    assert next(iterator) == 'ready'
    try:
        with pytest.raises(RuntimeError, match='ignored GeneratorExit'):
            iterator.close()
    finally:
        iterator.close()
    assert sys.gettrace() is original_trace
