from __future__ import absolute_import

import re
from typing import Any, List

import attr
from typing_extensions import TypedDict

import kslurm.test.args.models.formatters as formatters
from kslurm.args.arg_types import flag, keyword, shape
from kslurm.test.args.models.common import ModelTest, update_model


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


@attr.define
class AttrModel:
    time: str = shape(
        match=lambda arg: bool(re.match(r"^([0-9]{1,2}-)?[0-9]{1,2}:[0-9]{2}$", arg)),
        format=formatters.time,
        default="03:00",
    )

    gpu: bool = flag(match=["gpu"])

    number: int = shape(
        match=lambda arg: bool(re.match(r"^[0-9]+$", arg)), format=int, default="1"
    )

    job_template: list[int] = keyword(match=["-j", "--job-template"], num=1)

    length_5_keyword: list[str] = keyword(
        match=["--length_5_keyword"],
        num=5,
    )


# f = parse_args(["1:30", "gpu", "--job-template", "4", "5"], AttrModel)


class TypedDictModel(TypedDict):
    time: str
    gpu: bool
    number: str
    job_template: str
    length_5_keyword: str


attrmodel = AttrModel()

typed_dict_model = TypedDictModel(
    time=shape(
        match=lambda arg: bool(re.match(r"^([0-9]{1,2}-)?[0-9]{1,2}:[0-9]{2}$", arg)),
        format=formatters.time,
        default="03:00",
    ),
    gpu=flag(match=["gpu"]),
    number=shape(match=lambda arg: bool(re.match(r"^[0-9]+$", arg)), default="1"),
    job_template=keyword(match=["-j", "--job-template"], num=1),
    length_5_keyword=keyword(
        match=["--length_5_keyword"],
        num=5,
    ),
)

basic_attr = ModelTest(attrmodel, *get_tests(attrmodel))

basic_dict = ModelTest(typed_dict_model, *get_tests(typed_dict_model))
