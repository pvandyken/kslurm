from __future__ import absolute_import

import pytest
from hypothesis import given
from hypothesis import strategies as st

from kslurm.models import formatters
from kslurm.slurm.helpers import div_remainder, slurm_time_format


@given(num=st.integers(), denom=st.integers())
def test_div_remainder(num: int, denom: int):
    if denom == 0:
        with pytest.raises(AssertionError):
            div_remainder(num, denom)
    else:
        res, rem = div_remainder(num, denom)
        assert (res * denom) + rem == num


@given(min=st.integers(min_value=0))
def test_slurm_time_format(min: int):
    res = slurm_time_format(min)
    # Strip off last ":00", which won't be recognized by the formatter
    assert formatters.time(res[:-3]) == min
