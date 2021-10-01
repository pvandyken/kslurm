from __future__ import absolute_import

from typing import Any, List, NamedTuple

import pytest
from _pytest.fixtures import SubRequest

import kslurm.args.helpers as helpers
import kslurm.args.parser as sc
from kslurm.args import Arg
from kslurm.exceptions import CommandLineErrorGroup

from .models import models
from .models.common import ModelTest


class ModelCase(NamedTuple):
    model: object
    test: List[str]
    outcome: List[Arg[Any]]


@pytest.fixture(scope="module", params=models)
def model(request: SubRequest):  # type: ignore
    return request.param  # type: ignore


def test_relabelled_args_convert_back_to_model(model: ModelTest):
    labelled = helpers.get_arg_list(model.model)
    remodelled = helpers.update_model(labelled, model.model)
    assert remodelled == model.model


def test_parse_args(model: ModelTest):
    for args, outcome in zip(model.tests, model.expected_outcomes):
        if isinstance(outcome[0], Exception):
            try:
                sc.parse_args(args, model.model, True)
            except CommandLineErrorGroup as err_group:
                assert [err.msg for err in outcome] == [  # type: ignore
                    err.msg for err in err_group.sub_errors
                ]
            else:
                assert False
        else:
            parsed_model = sc.parse_args(args, model.model, True)
            labelled_list = helpers.get_arg_list(parsed_model)

            assert set(labelled_list) == set(outcome)  # type: ignore
