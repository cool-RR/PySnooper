import pytest

from pysnooper.utils import truncate


@pytest.mark.parametrize("max_length, expected", (
    (1, '.'),
    (2, '..'),
    (3, '...'),
    (4, '...p'),
    (8, 'ab...nop'),
))
def test_truncate_honors_small_and_normal_limits(max_length, expected):
    assert truncate('abcdefghijklmnop', max_length) == expected


def test_truncate_none_preserves_full_string():
    value = 'abcdefghijklmnop'
    assert truncate(value, None) == value


@pytest.mark.parametrize("value, max_length, expected", (
    ('', -3, '...'),
    ('', -1, '...'),
    ('a', -3, '...'),
    ('a', 0, '...'),
    ('abc', 0, 'a...bc'),
))
def test_truncate_preserves_nonpositive_legacy_behavior(
        value, max_length, expected):
    assert truncate(value, max_length) == expected
