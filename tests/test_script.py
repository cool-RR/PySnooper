from subprocess import Popen, PIPE
from sys import executable
from tempfile import NamedTemporaryFile


py_code = '''
def sub(a, b):
    return a - b


val = sub(1, 7)
print('val =', val)
'''


def run_pysnooper(options=None):
    tmp = NamedTemporaryFile()
    tmp.write(py_code.encode('ascii'))
    tmp.flush()

    # pysnooper emits output to stderr
    cmd = [executable, '-m', 'pysnooper']
    if options:
        cmd += options
    cmd += [tmp.name]
    proc = Popen(cmd, stderr=PIPE)
    assert proc.wait() == 0, 'error running pysnooper'

    return proc.stderr.read().decode('utf-8')


def test_script():
    out = run_pysnooper()
    for line in py_code.splitlines():
        assert line in out, '{!r} not found in output'.format(line)


def test_prefix():
    prefix = 'TEST_PYSNOOPR:'
    out = run_pysnooper(['--prefix', prefix])
    for line in out.splitlines():
        assert out.startswith(prefix), line


# TODO: test thread info
