# pyright: reportUnknownMemberType=false, reportUnknownArgumentType=false
from __future__ import absolute_import

from typing import Any, List, cast

from kslurm.args import Arg
from kslurm.args.arg_types import KeywordArg
from kslurm.args.helpers import get_arg_list


class ModelTest:
    def __init__(
        self,
        model: object,
        tests: List[List[str]],
        expected_outcomes: List[List[Arg[Any]]],
    ):
        self.model = model
        self.tests = tests
        self.expected_outcomes = expected_outcomes


def update_model(models: object, updates: List[Any]):
    arg_list = get_arg_list(models)
    ret = []
    for model, update in zip(arg_list, updates):
        if isinstance(update, list):
            val, values = update  # type: ignore
            assert isinstance(model, KeywordArg)
            if val is None:
                ret.append(model.add_values(values))
            else:
                ret.append(model.set_value(str(val)).add_values(values))
        elif update is None:
            ret.append(model)
        else:
            ret.append(model.set_value(str(update)))
    return cast(List[Arg[Any]], ret)
