# Copyright 2019 Ram Rachum.
# This program is distributed under the MIT license.

import setuptools


setuptools.setup(
    name='PySnooper',
    version='0.0.1',
    author='Ram Rachum',
    author_email='ram@rachum.com',
    description="A poor man's debugger for Python.",
    long_description=open('README.md', 'r').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/cool-RR/PySnooper',
    packages=setuptools.find_packages(),
    install_requires=open('requirements.txt', 'r').read().split('\n'), 
    tests_require=open('test_requirements.txt', 'r').read().split('\n'), 
    classifiers=[
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    
)