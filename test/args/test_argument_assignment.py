# pyright: reportPrivateUsage=false, reportUnknownArgumentType=false
from __future__ import absolute_import

import itertools as it

import pytest
from pytest import fixture

import kslurm.args.parser as sc
from kslurm.args import KeywordArg
from kslurm.args.arg_types import TailArg

from .arg_lists import DummyArgs
from .model_lists import positional_models


@fixture
def models():
    return positional_models(3)


@fixture
def args():
    return DummyArgs()


def test_get_keywork_group_size(args: DummyArgs):
    group_sizes = [sc._get_keyword_group_size(arg) for arg in args.two_keyword]
    assert group_sizes == [0, 0, 1, 0, 0, 5, 0, 0, 0, 0, 0, 0, 0, 0]


class TestGroupArgs:
    def test_collects_nonkeyword_into_empty_running_list(self, args: DummyArgs):
        arg_list = sc._group_args(args.two_keyword[0:2], [], None)
        assert list(arg_list) == args.two_keyword[0:2]

    def test_merges_args_with_keyword_according_to_group_size(self, args: DummyArgs):
        arg_list = sc._group_args(args.two_keyword[2:4], [], None)
        assert isinstance(args.two_keyword[2], KeywordArg)
        assert list(arg_list) == [
            args.two_keyword[2].add_values([args.two_keyword[3].value])
        ]

        arg_list = sc._group_args(args.two_keyword[5:11], [], None)
        assert isinstance(args.two_keyword[5], KeywordArg)
        assert list(arg_list) == [
            args.two_keyword[5].add_values(
                [model.raw_value for model in args.two_keyword[6:11]]
            )
        ]

    def test_continues_collecting_when_past_keyword_group(self, args: DummyArgs):
        arg_list = sc._group_args(args.two_keyword, [], None)
        assert isinstance(args.two_keyword[2], KeywordArg)
        assert isinstance(args.two_keyword[5], KeywordArg)
        assert list(arg_list) == list(
            it.chain(
                args.two_keyword[0:2],
                [args.two_keyword[2].add_values([args.two_keyword[3].raw_value])],
                args.two_keyword[4:5],
                [
                    args.two_keyword[5].add_values(
                        [model.raw_value for model in args.two_keyword[6:11]]
                    )
                ],
                args.two_keyword[11:],
            )
        )

    @pytest.mark.parametrize("count", [0, 1, 2, 3])
    def test_adds_right_amount_of_positional_args_before_tail(
        self, args: DummyArgs, count: int
    ):
        pos_models = positional_models(count)
        arg_list = sc._group_args(args.positional_patchwork, pos_models, TailArg())
        res = args.positional_patchwork[0 : (count * 2) + 1]
        if count < 3:
            res += [
                TailArg().add_values(
                    [
                        arg.raw_value
                        for arg in args.positional_patchwork[(count * 2) + 1 :]
                    ]
                )
            ]
        arg_l = list(arg_list)
        assert arg_l == res
        if count < 3:
            tail = arg_l[-1]
            assert isinstance(tail, TailArg)
            assert tail.raise_exception is False

    def test_records_exception_if_tail_args_present_but_no_model(self, args: DummyArgs):
        pos_models = positional_models(1)
        arg_list = sc._group_args(args.positional_patchwork, pos_models, None)
        tail = list(arg_list)[-1]
        assert isinstance(tail, TailArg)
        assert tail.raise_exception is True

    def test_does_not_capture_positional_argument_past_keyword_group(
        self, args: DummyArgs
    ):
        pos_models = positional_models(1)
        arg_list = sc._group_args(args.positional_wrapped_keyword, pos_models, None)
        model = args.positional_wrapped_keyword
        assert isinstance(model[2], KeywordArg)
        assert list(arg_list) == list(
            it.chain(
                model[0:2],
                [model[2].add_values([model[3].value])],
                [TailArg().add_values([model[4].raw_value])],
            )
        )

    def test_lazy_inf_keyword_consumes_until_shape_or_keyword(self, args: DummyArgs):
        model = args.lazy_keywords
        pos_models = positional_models(1)
        arg_list = sc._group_args(model, pos_models, None)
        assert isinstance(model[5], KeywordArg)
        assert isinstance(model[2], KeywordArg)
        assert list(arg_list) == list(
            it.chain(
                model[0:2],
                [model[2].add_values([model.value for model in model[3:5]])],
                [
                    model[5].add_values(  # type: ignore
                        [model.value for model in model[6:10]]
                    )
                ],
                model[10:],
            )
        )

    def test_greedy_inf_keyword_consumes_remaining_arguments(self, args: DummyArgs):
        model = args.greedy_keywords
        arg_list = sc._group_args(model, [], None)
        assert isinstance(model[2], KeywordArg)
        assert list(arg_list) == model[0:2] + [
            model[2].add_values([model.raw_value for model in model[3:]])
        ]
