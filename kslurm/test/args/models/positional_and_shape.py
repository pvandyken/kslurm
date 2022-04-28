from __future__ import absolute_import

import re
from test.args.models import formatters
from test.args.models.common import ModelTest, update_model
from typing import Any, List

import attr

from kslurm.args.arg_types import flag, keyword, positional, shape


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
    time: str = shape(
        match=lambda arg: bool(re.match(r"^([0-9]{1,2}-)?[0-9]{1,2}:[0-9]{2}$", arg)),
        format=formatters.time,
        default="03:00",
    )

    flag1: bool = flag(match=["flag"])

    cpu: int = shape(match=lambda arg: bool(re.match(r"^[0-9]+$", arg)), default="1")

    template: list[str] = keyword(match=["-j", "template"], num=1)

    positional1: str = positional(default="pos1")

    positional2: str = positional(default="pos2")

    positional3: str = positional(default="pos3")


pos_and_shape = ModelTest(
    PositionalAndShapeModel(), *get_tests(PositionalAndShapeModel())
)
