# Copyright 2019 Ram Rachum and collaborators.
# This program is distributed under the MIT license.

import pysnooper
from pysnooper.utils import ensure_tuple

def test_ensure_tuple():
    x1 = ('foo', ('foo',), ['foo'], {'foo'})
    assert set(map(ensure_tuple, x1)) == {('foo',)}

    x2 = (pysnooper.Keys('foo'), (pysnooper.Keys('foo'),),
          [pysnooper.Keys('foo')], {pysnooper.Keys('foo')})

    assert set(map(ensure_tuple, x2)) == {(pysnooper.Keys('foo'),)}





