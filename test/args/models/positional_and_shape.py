from __future__ import absolute_import

import re
from test.args.models import formatters
from test.args.models.common import ModelTest, update_model
from typing import Any, List

import attr

from kslurm.args.arg_types import FlagArg, KeywordArg, PositionalArg, ShapeArg, TailArg


def get_tests(model: object) -> List[List[List[Any]]]:
    return [
        [
            [
                "template",
                "parcour",
                "positional",
                "2",
                "positional2",
                "positional3",
            ]
        ],
        [
            update_model(
                model,
                [
                    "03:00",
                    None,
                    "2",
                    [True, ["parcour"]],
                    "positional",
                    "positional2",
                    "positional3",
                    [None, []],
                ],
            ),
        ],
    ]


@attr.s(auto_attribs=True)
class PositionalAndShapeModel:
    time: ShapeArg[str] = ShapeArg(
        id="random",
        match=lambda arg: bool(re.match(r"^([0-9]{1,2}-)?[0-9]{1,2}:[0-9]{2}$", arg)),
        format=formatters.time,
        value="03:00",
    )

    flag: FlagArg = FlagArg(match=["flag"])

    cpu: ShapeArg[str] = ShapeArg(
        match=lambda arg: bool(re.match(r"^[0-9]+$", arg)), value="1"
    )

    template: KeywordArg[str] = KeywordArg(match=["-j", "template"], num=1, value=False)

    positional: PositionalArg[str] = PositionalArg(id="positional", value="pos1")

    positional2: PositionalArg[str] = PositionalArg(id="positional2", value="pos2")

    positional3: PositionalArg[str] = PositionalArg(id="positional3", value="pos3")

    tail: TailArg = TailArg()


pos_and_shape = ModelTest(
    PositionalAndShapeModel(), *get_tests(PositionalAndShapeModel())
)
