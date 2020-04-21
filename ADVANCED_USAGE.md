# Advanced Usage #

Use `watch_explode` to expand values to see all their attributes or items of lists/dictionaries:

```python
@pysnooper.snoop(watch_explode=('foo', 'self'))
```

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

```console
$ export PYSNOOPER_DISABLED=1 # This makes PySnooper not do any snooping
```

This will output lines like:

```
Modified var:.. foo[2] = 'whatever'
New var:....... self.baz = 8
```

Start all snoop lines with a prefix, to grep for them easily:

```python
@pysnooper.snoop(prefix='ZZZ ')
```

Remove all machine-related data (paths, timestamps, memory addresses) to compare with other traces easily:

```python
@pysnooper.snoop(normalize=True)
```

On multi-threaded apps identify which thread are snooped in output:

```python
@pysnooper.snoop(thread_info=True)
```

PySnooper supports decorating generators.

If you decorate a class with `snoop`, it'll automatically apply the decorator to all the methods. (Not including properties and other special cases.)

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

Variables and exceptions get truncated to 100 characters by default. You
can customize that:

```python
    @pysnooper.snoop(max_variable_length=200)
```

You can also use `max_variable_length=None` to never truncate them.

Use `relative_time=True` to show timestamps relative to start time rather than
wall time.