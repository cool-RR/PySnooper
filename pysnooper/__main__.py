"""Run script under PySnooper"""

from subprocess import run
from argparse import ArgumentParser, FileType
from sys import executable
from os import environ, pathsep
from tempfile import mkdtemp


code = '''
from distutils.util import strtobool
from os import environ
import sys

from pysnooper.tracer import Tracer

options = {
    'prefix': environ.get('PYSNOOPER_PREFIX', ''),
    'thread_info': strtobool(environ.get('PYSNOOPER_THREAD_INFO', 'off')),
}

tracer = Tracer(**options)
tracer.trace_from_script = True
sys.settrace(tracer.trace)
'''


# TODO: Think about way to filter and --depth
def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument('script', help='python script', type=FileType('r'))
    parser.add_argument('--prefix', help='output line prefix', default='')
    parser.add_argument(
        '--thread-info', help='show thread information', default=False,
        action='store_true')
    args, rest = parser.parse_known_args()

    root = mkdtemp()
    with open(f'{root}/sitecustomize.py', 'w') as out:
        out.write(code)

    env = environ.copy()
    pypath = env.get('PYTHONPATH', '')
    if pypath:
        pypath = f'{root}{pathsep}{pypath}'
    else:
        pypath = root
    env['PYTHONPATH'] = pypath

    if args.prefix:
        env['PYSNOOPER_PREFIX'] = args.prefix
    if args.thread_info:
        env['PYSNOOPER_THREAD_INFO'] = 'yes'

    cmd = [executable, args.script.name] + rest
    run(cmd, env=env)


if __name__ == '__main__':
    main()
