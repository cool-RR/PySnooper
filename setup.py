# Copyright 2019 Ram Rachum.
# This program is distributed under the MIT license.

import setuptools

with open('README.md', 'r') as readme_file:
    long_description = readme_file.read()

setuptools.setup(
    name='PySnooper',
    version='0.0.1',
    author='Ram Rachum',
    author_email='ram@rachum.com',
    description="A poor man's debugger for Python.",
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/cool-RR/PySnooper',
    packages=setuptools.find_packages(),
    install_requires=('decorator>=4.3.0',), 
    tests_require=(
        'pytest>=4.4.1',
        'python_toolbox>=0.9.3',
    ), 
    classifiers=[
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    
)