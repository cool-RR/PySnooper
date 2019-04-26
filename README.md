# PySnooper - Never use print for debugging again #

[![Travis CI](https://img.shields.io/travis/cool-RR/PySnooper/master.svg)](https://travis-ci.org/cool-RR/PySnooper)

**PySnooper** is a poor man's debugger.

You're trying to figure out why your Python code isn't doing what you think it should be doing. You'd love to use a full-fledged debugger with breakpoints and watches, but you can't be bothered to set one up right now.

You want to know which lines are running and which aren't, and what the values of the local variables are.

Most people would use `print` lines, in strategic locations, some of them showing the values of variables.

**PySnooper** lets you do the same, except instead of carefully crafting the right `print` lines, you just add one decorator line to the function you're interested in. You'll get a play-by-play log of your function, including which lines ran and   when, and exactly when local variables were changed.

What makes **PySnooper** stand out from all other code intelligence tools? You can use it in your shitty, sprawling enterprise codebase without having to do any setup. Just slap the decorator on, as shown below, and redirect the output to a dedicated log file by specifying its path as the first argument.

# Example #

We're writing a function that converts a number to binary, by returning a list of bits. Let's snoop on it by adding the `@pysnooper.snoop()` decorator:

```python
import pysnooper

@pysnooper.snoop()
def number_to_bits(number):
    if number:
        bits = []
        while number:
            number, remainder = divmod(number, 2)
            bits.insert(0, remainder)
        return bits
    else:
        return [0]

number_to_bits(6)
```
The output to stderr is:

```
Starting var:.. number = 6
15:29:11.327032 call         4 def number_to_bits(number):
15:29:11.327032 line         5     if number:
15:29:11.327032 line         6         bits = []
New var:....... bits = []
15:29:11.327032 line         7         while number:
15:29:11.327032 line         8             number, remainder = divmod(number, 2)
New var:....... remainder = 0
Modified var:.. number = 3
15:29:11.327032 line         9             bits.insert(0, remainder)
Modified var:.. bits = [0]
15:29:11.327032 line         7         while number:
15:29:11.327032 line         8             number, remainder = divmod(number, 2)
Modified var:.. number = 1
Modified var:.. remainder = 1
15:29:11.327032 line         9             bits.insert(0, remainder)
Modified var:.. bits = [1, 0]
15:29:11.327032 line         7         while number:
15:29:11.327032 line         8             number, remainder = divmod(number, 2)
Modified var:.. number = 0
15:29:11.327032 line         9             bits.insert(0, remainder)
Modified var:.. bits = [1, 1, 0]
15:29:11.327032 line         7         while number:
15:29:11.327032 line        10         return bits
15:29:11.327032 return      10         return bits
Return value:.. [1, 1, 0]
```

# Features #

If stderr is not easily accessible for you, you can redirect the output to a file:

```python
@pysnooper.snoop('/my/log/file.log')
```

See values of some variables that aren't local variables:

```python
@pysnooper.snoop(variables=('foo.bar', 'self.whatever'))
```

Show snoop lines for functions that your function calls:

```python
@pysnooper.snoop(depth=2)
```

Start all snoop lines with a prefix, to grep for them easily:

```python
@pysnooper.snoop(prefix='ZZZ ')
```

# Installation #

```console
$ pip install pysnooper
```

# Contribute #

[Pull requests](https://github.com/cool-RR/PySnooper/pulls) are always welcome!
Please, write tests and run them with [Tox](https://tox.readthedocs.io/).

Tox installs all dependencies automatically. You only need to install Tox itself:

```console
$ pip install tox
```

List all environments `tox` would run:

```console
$ tox -lv
```

If you want to run tests against all target Python versions use [pyenv](
https://github.com/pyenv/pyenv) to install them. Otherwise, you can run
only linters and the ones you have already installed on your machine:

```console
# run only some environments
$ tox -e flake8,pylint,bandit,py27,py36
```

Tests should pass before you push your code. They will be run again on Travis CI.

# License #

Copyright (c) 2019 Ram Rachum and collaborators, released under the MIT license.

I provide [Development services in Python and Django](https://chipmunkdev.com
) and I [give Python workshops](http://pythonworkshops.co/) to teach people
Python and related topics.

# Media Coverage #

[Hacker News thread](https://news.ycombinator.com/item?id=19717786)
and [/r/Python Reddit thread](https://www.reddit.com/r/Python/comments/bg0ida/pysnooper_never_use_print_for_debugging_again/) (22 April 2019)
