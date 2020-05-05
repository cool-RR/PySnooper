# Copyright 2019 Ram Rachum and collaborators.
# This program is distributed under the MIT license.

import pytest

from . import mini_toolbox


def test_output_capturer_doesnt_swallow_exceptions():
    with pytest.raises(ZeroDivisionError):
        with mini_toolbox.OutputCapturer():
            1 / 0
