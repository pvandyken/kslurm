from __future__ import absolute_import

from typing import Tuple


def div_remainder(num: int, denom: int) -> Tuple[int, int]:
    assert denom != 0
    remainder = num % denom
    return (num - remainder) // denom, remainder


def slurm_time_format(min: int) -> str:
    hr, ex_min = div_remainder(min, 60)
    days, ex_hr = div_remainder(hr, 24)
    if days:
        return f"{days}-{ex_hr:02d}:{ex_min:02d}:00"
    else:
        return f"{ex_hr:02d}:{ex_min:02d}:00"
