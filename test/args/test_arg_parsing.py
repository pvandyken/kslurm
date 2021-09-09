from pytest import fixture
from typing import List, cast, Any
import functools as ft
import cluster_utils.args.parser as sc
from cluster_utils.args import Arg, KeywordArg

from .parser_dummy_args import Models as dummy_models, ArgList, DummyArgs

@fixture
def models():
    return dummy_models()

@fixture
def args():
    return DummyArgs()

def test_get_keywork_group_size(args: DummyArgs):
    group_sizes = [sc.get_keyword_group_size(arg) for arg in args.two_keyword]
    assert group_sizes == [0, 0, 1, 0, 0, 5, 0, 0, 0, 0, 0, 0, 0, 0]

class TestGroupKeywords:
    def _reduce_arg_list(self, args: List[Arg[Any]]):
        return  ft.reduce(
                    sc.group_keyword, args, (0, cast(List[Arg[Any]], []))
                )
    
    def test_collects_nonkeyword_into_empty_running_list(self, args: DummyArgs):
        first = sc.group_keyword((0, []), args.two_keyword[0]) 
        group_size, arg_list = sc.group_keyword(first, args.two_keyword[1]) 
        assert group_size == 0
        assert list(arg_list) == args.two_keyword[0:2]
    
    def test_adds_keyword_and_updates_group_number(self, args: DummyArgs):
        group_size, arg_list = sc.group_keyword((0, []), args.two_keyword[2])
        assert group_size == 1
        assert list(arg_list) == [args.two_keyword[2]]

    def test_merges_args_with_keyword_according_to_group_size(self, args: DummyArgs):
        first = sc.group_keyword((0, []), args.two_keyword[2])
        group_size, arg_list = sc.group_keyword(first, args.two_keyword[3])
        assert group_size == 0
        assert isinstance(args.two_keyword[2], KeywordArg)
        assert list(arg_list) == [args.two_keyword[2].add_values([args.two_keyword[3].value])]

        first = sc.group_keyword((0, []), args.two_keyword[5])
        second = sc.group_keyword(first, args.two_keyword[6])
        third = sc.group_keyword(second, args.two_keyword[7])
        fourth = sc.group_keyword(third, args.two_keyword[8])
        fifth = sc.group_keyword(fourth, args.two_keyword[9])
        group_size, arg_list = sc.group_keyword(fifth, args.two_keyword[10])
        assert group_size == 0
        assert isinstance(args.two_keyword[5], KeywordArg)
        assert list(arg_list) == [args.two_keyword[5].add_values([
            model.value for model in args.two_keyword[6:11]
        ])]

    def test_can_use_reduce_to_traverse_long_arg_lists(self, args: DummyArgs):
        group_size, arg_list = \
            self._reduce_arg_list(args.two_keyword[5:6])
        assert group_size == 5
        assert isinstance(args.two_keyword[5], KeywordArg)
        assert list(arg_list) == [args.two_keyword[5]]

        group_size, arg_list = \
            self._reduce_arg_list(args.two_keyword[5:11])
        assert group_size == 0
        assert list(arg_list) == [args.two_keyword[5].add_values([
            model.value for model in args.two_keyword[6:11]
        ])]

    def test_continues_collecting_when_past_keyword_group(self, args: DummyArgs):
        group_size, arg_list = \
            self._reduce_arg_list(args.two_keyword)
        assert isinstance(args.two_keyword[2], KeywordArg)
        assert isinstance(args.two_keyword[5], KeywordArg)
        assert group_size == 0
        assert list(arg_list) == \
            args.two_keyword[0:2] + \
            [args.two_keyword[2].add_values([args.two_keyword[3].value])] + \
            args.two_keyword[4:5] + \
            [args.two_keyword[5].add_values([
                model.value for model in args.two_keyword[6:11]
            ])] + \
            args.two_keyword[11:]

    def test_does_not_capture_positional_argument_past_keyword_group(self, args: DummyArgs):
        group_size, arg_list = \
            self._reduce_arg_list(args.positional_wrapped_keyword)
        model = args.positional_wrapped_keyword
        assert isinstance(model[2], KeywordArg)
        assert group_size == 0
        assert list(arg_list) == \
            model[0:2] + \
            [model[2].add_values([model[3].value])] + \
            model[4:]
    
    def test_lazy_inf_keyword_consumes_until_shape_or_keyword(self, args: DummyArgs):
        model = args.lazy_keywords
        group_size, arg_list = \
            self._reduce_arg_list(model)
        assert isinstance(model[5], KeywordArg)
        assert isinstance(model[2], KeywordArg)
        assert group_size == 0
        assert list(arg_list) == \
            model[0:2] + \
            [model[2].add_values([
                model.value for model in model[3:5]
            ])] + \
            [model[5].add_values([ 
                model.value for model in model[6:10]
            ])] + \
            model[10:]
    
    def test_greedy_inf_keyword_consumes_remaining_arguments(self, args: DummyArgs):
        model = args.greedy_keywords
        group_size, arg_list = \
            self._reduce_arg_list(model)
        assert isinstance(model[2], KeywordArg)
        assert group_size == -7
        assert list(arg_list) == \
            model[0:2] + \
            [model[2].add_values([
                model.value for model in model[3:]
            ])]


def test_group_keyword_correctly_forms_groups(args: DummyArgs):

    two = sc.group_keywords(args.two_keyword)
    pos_wrapped = sc.group_keywords(args.positional_wrapped_keyword)
    lazy = sc.group_keywords(args.lazy_keywords)
    greedy = sc.group_keywords(args.greedy_keywords)

    assert list(two) == [
        ArgList.time,
        ArgList.gpu,
        ArgList.job_template.add_values([
            ArgList.positional.value
        ]),
        ArgList.time,
        ArgList.length_5_keyword.add_values([
            ArgList.positional.value,
            ArgList.time.value,
            ArgList.gpu.value,
            ArgList.positional.value,
            ArgList.positional.value
        ]),
        ArgList.gpu,
        ArgList.positional,
        ArgList.positional
    ]

    assert list(pos_wrapped) == [
        ArgList.time,
        ArgList.positional,
        ArgList.job_template.add_values([
            ArgList.positional.value
        ]),
        ArgList.positional
    ]

    assert list(lazy) == [
        ArgList.time,
        ArgList.positional,
        ArgList.lazy_inf_keyword.add_values([
            ArgList.positional.value,
            ArgList.positional.value
        ]),
        ArgList.lazy_inf_keyword.add_values([
            ArgList.positional.value,
            ArgList.positional.value,
            ArgList.positional.value,
            ArgList.positional.value
        ]),
        ArgList.time
    ]

    assert list(greedy) == [
        ArgList.time,
        ArgList.positional,
        ArgList.greedy_inf_keyword.add_values([
            ArgList.positional.value,
            ArgList.time.value,
            ArgList.lazy_inf_keyword.value,
            ArgList.time.value,
            ArgList.positional.value,
            ArgList.time.value
        ])
    
    ]

class TestDelineateCommand:
    def test_assigns_positionals_to_models(self, models: dummy_models, args: DummyArgs):
        model = models.three_positionals
        arg_set = args.positionals
        labelled, extras = sc.delineate_positional(arg_set, model)

        assert list(labelled) == [
            ArgList.positional.set_value("Hello"),
            ArgList.positional2.set_value("beautiful"),
            ArgList.positional3.set_value("world")
        ]

        assert extras == []

    def test_passes_extras(self, models: dummy_models, args: DummyArgs):
        model = models.three_positionals
        arg_set = args.extra_positionals
        
        labelled, extras = sc.delineate_positional(arg_set, model)

        
        assert list(labelled) == [
            ArgList.positional.set_value("Hello"),
            ArgList.positional2.set_value("beautiful"),
            ArgList.positional3.set_value("world"),
        ]

        assert extras == [
            ArgList.positional3.set_value("Here"),
            ArgList.positional3.set_value("Be"),
            ArgList.positional3.set_value("Extra!"),
        ]

