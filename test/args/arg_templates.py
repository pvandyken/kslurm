from __future__ import absolute_import

import re
from typing import Union

from kslurm.args.arg_types import FlagArg, KeywordArg, PositionalArg, ShapeArg, TailArg


def time_format(time: str):
    if "-" in time:
        days, hhmm = time.split("-")
        hours, min = hhmm.split(":")
    else:
        days = 0
        hours, min = time.split(":")
    return str(int(min) + int(hours) * 60 + int(days) * 60 * 24)


class Templates:
    time: ShapeArg[str] = ShapeArg(
        id="random",
        match=lambda arg: bool(re.match(r"^([0-9]{1,2}-)?[0-9]{1,2}:[0-9]{2}$", arg)),
        format=time_format,
        value="03:00",
    )

    gpu: FlagArg = FlagArg(match=["gpu"])

    number: ShapeArg[int] = ShapeArg(
        match=lambda arg: bool(re.match(r"^[0-9]+$", arg)), value="1", format=int
    )

    job_template: KeywordArg[str] = KeywordArg[str](
        id="junk", match=["-j", "--job-template"], num=1, value=False
    )

    length_5_keyword: KeywordArg[str] = KeywordArg[str](
        id="length_5_keyword",
        match=["--length_5_keyword"],
        num=5,
        value=False,
    )

    lazy_inf_keyword: KeywordArg[str] = KeywordArg[str](
        id="lazy_inf_keyword",
        match=["lazy_inf_keyword"],
        num=-1,
        value=False,
        lazy=True,
    )

    greedy_inf_keyword: KeywordArg[Union[str, bool]] = KeywordArg[Union[str, bool]](
        id="greedy_inf_keyword",
        match=["greedy_inf_keyword"],
        num=-1,
        value=False,
    )

    positional: PositionalArg[str] = PositionalArg(id="positional", value="pos1")

    positional2: PositionalArg[str] = PositionalArg(id="positional2", value="pos2")

    positional3: PositionalArg[str] = PositionalArg(id="positional3", value="pos3")

    positional4: PositionalArg[str] = PositionalArg(id="positional4", value="pos4")

    positional5: PositionalArg[str] = PositionalArg(id="positional5", value="pos5")

    tail: TailArg = TailArg()
