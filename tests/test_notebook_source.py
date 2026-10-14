import io
import linecache

import pytest

import pysnooper


@pytest.mark.parametrize('filename', (
    '/tmp/ipykernel_12345/123456789.py',
    '/custom/temp/ipykernel_12345/123456789.py',
    '/var/folders/ab/cd/T/ipykernel_12345/123456789.py',
    r'C:\Users\example\AppData\Local\Temp\ipykernel_12345\123456789.py',
))
def test_ipykernel_source_from_linecache(monkeypatch, filename):
    source = ('def notebook_function(value):\n'
              '    result = value + 1\n'
              '    return result\n')
    monkeypatch.setitem(linecache.cache, filename,
                        (len(source), None, source.splitlines(True), filename))
    monkeypatch.setattr('pysnooper.tracer.source_and_path_cache', {})
    namespace = {'__name__': '__main__'}
    exec(compile(source, filename, 'exec'), namespace)
    output = io.StringIO()
    function = pysnooper.snoop(output, color=False)(
        namespace['notebook_function'])

    assert function(41) == 42
    trace = output.getvalue()
    assert 'SOURCE IS UNAVAILABLE' not in trace
    assert 'def notebook_function(value):' in trace
    assert '    result = value + 1' in trace
    assert '    return result' in trace
    assert 'Return value:.. 42' in trace


def test_ipykernel_source_from_file_when_not_cached(monkeypatch, tmpdir):
    filename = tmpdir.mkdir('ipykernel_12345').join('123456789.py')
    source = 'def notebook_function():\n    return 42\n'
    filename.write(source)
    filename = str(filename)
    monkeypatch.delitem(linecache.cache, filename, raising=False)
    monkeypatch.setattr('pysnooper.tracer.source_and_path_cache', {})
    namespace = {'__name__': '__main__'}
    exec(compile(source, filename, 'exec'), namespace)
    output = io.StringIO()
    function = pysnooper.snoop(output, color=False)(
        namespace['notebook_function'])

    assert function() == 42
    trace = output.getvalue()
    assert 'SOURCE IS UNAVAILABLE' not in trace
    assert 'def notebook_function():' in trace
    assert '    return 42' in trace
