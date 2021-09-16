import pytest
from _pytest.fixtures import SubRequest
from typing import Union, cast
import re

import kslurm.args.parser as sc
import kslurm.args.helpers as helpers
from kslurm.args import ShapeArg, KeywordArg

from .arg_lists import ArgStr
from .dummy_models import AttrModel, TypedDictModel, typed_dict_model, time


ModelTypes = Union[AttrModel, TypedDictModel]


@pytest.fixture(scope="module", params=[AttrModel(), typed_dict_model])
def model(request: SubRequest) -> ModelTypes:
    return cast(ModelTypes, request.param) # type: ignore

@pytest.fixture
def arg_list() -> ArgStr:
    return ArgStr()


def test_relabel_args_turns_keys_into_ids(model: ModelTypes):
    labelled = helpers.get_arg_list(model)
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
            match=['-j', '--job-template'],
            num=1,
            value=False),
    ]

def test_relabelled_args_convert_back_to_model(model: ModelTypes):
    labelled = helpers.get_arg_list(model)
    remodelled = helpers.update_model(labelled, model)
    assert remodelled == model

class TestParseArgs:
    def test_two_keywords_no_positionals_with_tail(self, model: ModelTypes, arg_list: ArgStr):
        arg = arg_list.two_keyword
        parsed_model = sc.parse_args(arg, model)
        labelled_list = helpers.get_arg_list(parsed_model)
        print(labelled_list)
        assert AttrModel().time.set_value("07:23").setid("time") in labelled_list
        assert AttrModel().tail.add_values(["command"]) in labelled_list