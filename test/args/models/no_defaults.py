from __future__ import absolute_import

import re
import test.args.models.formatters as formatters
from test.args.models.common import ModelTest, update_model
from typing import Any, List

import attr
from typing_extensions import TypedDict

from kslurm.args.arg_types import FlagArg, KeywordArg, ShapeArg, TailArg
from kslurm.exceptions import MandatoryArgError


def get_tests(model: object) -> List[List[List[Any]]]:
    return [
        [
            # Providing everything works
            [
                "07:23",
                "gpu",
                "3",
                "--length_5_keyword",
                "one",
                "of",
                "the",
                "five",
                "values",
                "command",
            ],
            # Raise Exception if missing stuff
            ["gpu"],
        ],
        [
            update_model(
                model,
                [
                    "07:23",
                    True,
                    3,
                    [True, ["one", "of", "the", "five", "values"]],
                    [None, ["command"]],
                ],
            ),
            [
                MandatoryArgError("time has not been provided a value."),
                MandatoryArgError("number has not been provided a value."),
                MandatoryArgError("--length_5_keyword has not been provided a value."),
            ],
        ],
    ]


@attr.s(auto_attribs=True)
class AttrModel:
    time: ShapeArg[str] = ShapeArg(
        id="random",
        match=lambda arg: bool(re.match(r"^([0-9]{1,2}-)?[0-9]{1,2}:[0-9]{2}$", arg)),
        format=formatters.time,
    )

    gpu: FlagArg = FlagArg(match=["gpu"])

    number: ShapeArg[int] = ShapeArg(
        match=lambda arg: bool(re.match(r"^[0-9]+$", arg)), format=int
    )

    length_5_keyword: KeywordArg[str] = KeywordArg(
        id="length_5_keyword",
        match=["--length_5_keyword"],
        num=5,
        value=None,
    )

    tail: TailArg = TailArg()


class TypedDictModel(TypedDict):
    time: ShapeArg[str]
    gpu: FlagArg
    number: ShapeArg[str]
    length_5_keyword: KeywordArg[str]
    tail: TailArg


attrmodel = AttrModel()

typed_dict_model = TypedDictModel(
    time=ShapeArg(
        id="random",
        match=lambda arg: bool(re.match(r"^([0-9]{1,2}-)?[0-9]{1,2}:[0-9]{2}$", arg)),
        format=formatters.time,
    ),
    gpu=FlagArg(match=["gpu"]),
    number=ShapeArg(match=lambda arg: bool(re.match(r"^[0-9]+$", arg))),
    length_5_keyword=KeywordArg[str](
        id="length_5_keyword",
        match=["--length_5_keyword"],
        num=5,
        value=None,
    ),
    tail=TailArg(),
)

no_default_attr = ModelTest(attrmodel, *get_tests(attrmodel))

no_default_dict = ModelTest(typed_dict_model, *get_tests(typed_dict_model))
