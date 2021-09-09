import pytest
from _pytest.fixtures import SubRequest
from typing import Union, cast
import re

import cluster_utils.args.parser as sc
from cluster_utils.args import ShapeArg, KeywordArg

from .parser_dummy_args import ArgStr
from .dummy_models import AttrModel, TypedDictModel, typed_dict_model, time


ModelTypes = Union[AttrModel, TypedDictModel]


@pytest.fixture(scope="module", params=[AttrModel(), typed_dict_model])
def model(request: SubRequest) -> ModelTypes:
    return cast(ModelTypes, request.param)

@pytest.fixture
def arg_list() -> ArgStr:
    return ArgStr()


def test_relabel_args_turns_keys_into_ids(model: ModelTypes):
    labelled = sc.relabel_args(model)
    assert labelled[0:4] == [
        ShapeArg(
            id = "time",
            match = lambda arg: bool(re.match(r'^([0-9]{1,2}-)?[0-9]{1,2}:[0-9]{2}$', arg)),
            format = time,
            value = "03:00"),

        ShapeArg(
            id = "gpu",
            match = lambda arg: arg == "gpu",
            value="gpu"),

        ShapeArg(
            id = "cpu",
            match = lambda arg: bool(re.match(r'^[0-9]+$', arg)),
            value = "1"),

        KeywordArg(
            id="job_template", 
            match=lambda arg : arg == '-j' or arg == '--job-template',
            num=1,
            value="job_template"),
    ]

def test_relabelled_args_convert_back_to_model(model: ModelTypes):
    labelled = sc.relabel_args(model)
    remodelled = sc.update_model(labelled, model)
    assert remodelled == model

class TestParseArgs:
    def test_two_keywords_no_positionals_with_tail(self, model: ModelTypes, arg_list: ArgStr):
        arg = arg_list.two_keyword
        parsed_model = sc.parse_args(arg, model)
        labelled_list = sc.relabel_args(parsed_model)
        print(labelled_list)
        assert AttrModel().time.set_value("07:23").setid("time") in labelled_list
        assert AttrModel().tail.add_values(["command"]) in labelled_list