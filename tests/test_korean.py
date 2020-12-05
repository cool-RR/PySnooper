# -*- coding: utf-8 -*-
import pytest
import pysnooper

@pysnooper.snoop()
def func(x):
    return x + 1
def test_korean(x):
    assert func(x) != x+1, '성공!'
test_korean(0)
