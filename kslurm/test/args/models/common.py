# pyright: reportUnknownMemberType=false, reportUnknownArgumentType=false
from __future__ import absolute_import

from typing import Any, List

from kslurm.args.arg import Arg
from kslurm.args.helpers import get_arg_list


class ModelTest:
    def __init__(
        self,
        model: object,
        tests: List[List[str]],
        expected_outcomes: List[List[Arg[Any, Any]]],
    ):
        self.model = model
        self.tests = tests
        self.expected_outcomes = expected_outcomes


def update_model(models: object, updates: List[Any]):
    arg_list = get_arg_list(models.__class__)
    ret: list[Arg[Any, Any]] = []
    for model, update in zip(arg_list, updates):
        if isinstance(update, list):
            val, values = update  # type: ignore
            if val is None:
                ret.append(model.with_values(values))
            else:
                ret.append(model.with_value(str(val)).with_values(values))
        elif update is None:
            ret.append(model)
        else:
            ret.append(model.with_value(str(update)))
    return ret
