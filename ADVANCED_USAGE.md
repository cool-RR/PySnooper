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

```console
$ export PYSNOOPER_DISABLED=1 # This makes PySnooper not do any snooping
```

# License #

Copyright (c) 2019 Ram Rachum and collaborators, released under the MIT license.

I provide [Development services in Python and Django](https://chipmunkdev.com
) and I [give Python workshops](http://pythonworkshops.co/) to teach people
Python and related topics.

# Media Coverage #

[Hacker News thread](https://news.ycombinator.com/item?id=19717786)
and [/r/Python Reddit thread](https://www.reddit.com/r/Python/comments/bg0ida/pysnooper_never_use_print_for_debugging_again/) (22 April 2019)
