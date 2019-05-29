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

Or if you don't want to trace an entire function, you can wrap the relevant part in a `with` block:

```python
import pysnooper
import random

def foo():
    lst = []
    for i in range(10):
        lst.append(random.randrange(1, 1000))

    with pysnooper.snoop():
        lower = min(lst)
        upper = max(lst)
        mid = (lower + upper) / 2
        print(lower, mid, upper)

foo()
```

which outputs something like:

```
New var:....... i = 9
New var:....... lst = [681, 267, 74, 832, 284, 678, ...]
09:37:35.881721 line        10         lower = min(lst)
New var:....... lower = 74
09:37:35.882137 line        11         upper = max(lst)
New var:....... upper = 832
09:37:35.882304 line        12         mid = (lower + upper) / 2
74 453.0 832
New var:....... mid = 453.0
09:37:35.882486 line        13         print(lower, mid, upper)
```

# Features #

If stderr is not easily accessible for you, you can redirect the output to a file:

```python
@pysnooper.snoop('/my/log/file.log')
```

You can also pass a stream or a callable instead, and they'll be used.

See values of some expressions that aren't local variables:

```python
@pysnooper.snoop(watch=('foo.bar', 'self.x["whatever"]'))
```

Expand values to see all their attributes or items of lists/dictionaries:

```python
@pysnooper.snoop(watch_explode=('foo', 'self'))
```

This will output lines like:

```
Modified var:.. foo[2] = 'whatever'
New var:....... self.baz = 8
```

(see [Advanced Usage](#advanced-usage) for more control)

Show snoop lines for functions that your function calls:

```python
@pysnooper.snoop(depth=2)
```

Start all snoop lines with a prefix, to grep for them easily:

```python
@pysnooper.snoop(prefix='ZZZ ')
```

On multi-threaded apps identify which thread are snooped in output:

```python
@pysnooper.snoop(thread_info=True)
```

PySnooper supports decorating generators.

You can also customize the repr of an object:

```python
def large(l):
    return isinstance(l, list) and len(l) > 5

def print_list_size(l):
    return 'list(size={})'.format(len(l))

def print_ndarray(a):
    return 'ndarray(shape={}, dtype={})'.format(a.shape, a.dtype)

@pysnooper.snoop(custom_repr=((large, print_list_size), (numpy.ndarray, print_ndarray)))
def sum_to_x(x):
    l = list(range(x))
    a = numpy.zeros((10,10))
    return sum(l)

sum_to_x(10000)
```

You will get `l = list(size=10000)` for the list, and `a = ndarray(shape=(10, 10), dtype=float64)` for the ndarray.
The `custom_repr` are matched in order, if one condition matches, no further conditions will be checked.

# Installation #

You can install **PySnooper** by:

* pip:
```console
$ pip install pysnooper
```

* conda with conda-forge channel:
```console
$ conda install -c conda-forge pysnooper
```

# Advanced Usage #

`watch_explode` will automatically guess how to expand the expression passed to it based on its class. You can be more specific by using one of the following classes:

```python
import pysnooper

@pysnooper.snoop(watch=(
    pysnooper.Attrs('x'),    # attributes
    pysnooper.Keys('y'),     # mapping (e.g. dict) items
    pysnooper.Indices('z'),  # sequence (e.g. list/tuple) items
))
```

Exclude specific keys/attributes/indices with the `exclude` parameter, e.g. `Attrs('x', exclude=('_foo', '_bar'))`.

Add a slice after `Indices` to only see the values within that slice, e.g. `Indices('z')[-3:]`.

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

Or just install project in developer mode with test dependencies:

``` bash
$ pip install -e path/to/PySnooper[tests]
```

And run tests:

``` bash
$ pytest
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
