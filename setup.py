"""
Packaging implementation for PySnooper

Copyright 2019 Ram Rachum.
This program is distributed under the MIT license.
"""
import setuptools


def read_file(filename):
    """Return the contents of a file"""
    with open(filename) as file:
        return file.read()


setuptools.setup(
    name='PySnooper',
    version='0.0.11',
    author='Ram Rachum',
    author_email='ram@rachum.com',
    description="A poor man's debugger for Python.",
    long_description=read_file('README.md'),
    long_description_content_type='text/markdown',
    url='https://github.com/cool-RR/PySnooper',
    packages=setuptools.find_packages(exclude=['tests']),
    install_requires=read_file('requirements.in'),
    classifiers=[
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Topic :: Software Development :: Debuggers',
    ],
)
