"""Run script under PySnooper"""

from subprocess import run
from argparse import ArgumentParser, FileType
from sys import executable
from os import environ, pathsep
from tempfile import mkdtemp


code = '''
import pysnooper


pysnooper.snoop().__enter__()
'''


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument('script', help='python script', type=FileType('r'))
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

    cmd = [executable, args.script.name] + rest
    run(cmd, env=env)


if __name__ == '__main__':
    main()
