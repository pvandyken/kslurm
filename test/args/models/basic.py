from __future__ import absolute_import

import re
import test.args.models.formatters as formatters
from test.args.models.common import ModelTest, update_model
from typing import Any, List

import attr
from typing_extensions import TypedDict

from kslurm.args.arg_types import FlagArg, KeywordArg, ShapeArg, TailArg


def get_tests(model: object) -> List[List[List[Any]]]:
    return [
        [
            [
                "07:23",
                "gpu",
                "--job-template",
                "parcour",
                "3",
                "--length_5_keyword",
                "one",
                "of",
                "the",
                "five",
                "values",
                "command",
            ],
            # Fall back on defaults
            [
                "3",
                "command",
                "of",
                "--length_5_keyword",
                "five",
                "07:23",
                "--job-template",
                "parcour",
                "the",
                "one",
                "values",
                "gpu",
            ],
            # Keyword masking shapes and flags
            [
                "07:23",
                "--length_5_keyword",
                "command",
                "gpu",
                "3",
                "--job-template",
                "parcour",
                "10",
                "of",
                "five",
                "the",
                "one",
                "values",
            ],
        ],
        [
            update_model(
                model,
                [
                    "07:23",
                    True,
                    3,
                    [True, ["parcour"]],
                    [True, ["one", "of", "the", "five", "values"]],
                    [None, ["command"]],
                ],
            ),
            update_model(
                model,
                [
                    None,
                    None,
                    3,
                    None,
                    None,
                    [
                        None,
                        [
                            "command",
                            "of",
                            "--length_5_keyword",
                            "five",
                            "07:23",
                            "--job-template",
                            "parcour",
                            "the",
                            "one",
                            "values",
                            "gpu",
                        ],
                    ],
                ],
            ),
            update_model(
                model,
                [
                    "07:23",
                    None,
                    "10",
                    None,
                    [True, ["command", "gpu", "3", "--job-template", "parcour"]],
                    [None, ["of", "five", "the", "one", "values"]],
                ],
            ),
        ],
    ]


@attr.s(auto_attribs=True)
class AttrModel:
    time: ShapeArg[str] = ShapeArg(
        id="random",
        match=lambda arg: bool(re.match(r"^([0-9]{1,2}-)?[0-9]{1,2}:[0-9]{2}$", arg)),
        format=formatters.time,
        value="03:00",
    )

    gpu: FlagArg = FlagArg(match=["gpu"])

    number: ShapeArg[int] = ShapeArg(
        match=lambda arg: bool(re.match(r"^[0-9]+$", arg)), format=int, value="1"
    )

    job_template: KeywordArg[str] = KeywordArg(
        id="junk", match=["-j", "--job-template"], num=1, value=False
    )

    length_5_keyword: KeywordArg[str] = KeywordArg(
        id="length_5_keyword",
        match=["--length_5_keyword"],
        num=5,
        value=False,
    )

    tail: TailArg = TailArg()


class TypedDictModel(TypedDict):
    time: ShapeArg[str]
    gpu: FlagArg
    number: ShapeArg[str]
    job_template: KeywordArg[str]
    length_5_keyword: KeywordArg[str]
    tail: TailArg


attrmodel = AttrModel()

typed_dict_model = TypedDictModel(
    time=ShapeArg(
        id="random",
        match=lambda arg: bool(re.match(r"^([0-9]{1,2}-)?[0-9]{1,2}:[0-9]{2}$", arg)),
        format=formatters.time,
        value="03:00",
    ),
    gpu=FlagArg(match=["gpu"]),
    number=ShapeArg(match=lambda arg: bool(re.match(r"^[0-9]+$", arg)), value="1"),
    job_template=KeywordArg[str](
        id="junk", match=["-j", "--job-template"], num=1, value=False
    ),
    length_5_keyword=KeywordArg[str](
        id="length_5_keyword",
        match=["--length_5_keyword"],
        num=5,
        value=False,
    ),
    tail=TailArg(),
)

basic_attr = ModelTest(attrmodel, *get_tests(attrmodel))

basic_dict = ModelTest(typed_dict_model, *get_tests(typed_dict_model))
