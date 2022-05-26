# pyright: reportPrivateUsage=false, reportUnknownArgumentType=false
from __future__ import absolute_import

from copy import copy
from typing import Any, NamedTuple

import hypothesis.strategies as st
from hypothesis import assume, given

import kslurm.args.parser as sc
from kslurm.args import matchers
from kslurm.args.arg import Arg, Context

CliParams = NamedTuple(
    "CliParams",
    [
        ("argv", list[str]),
        ("models", dict[str, Arg[Any, Any]]),
        ("results", dict[str, Arg[Any, Any]]),
        ("tail", list[str]),
    ],
)


@st.composite
def cli_params(draw: st.DrawFn):
    alphabet = st.characters(blacklist_categories=("Cs", "Zs"))
    number = draw(st.integers(min_value=0, max_value=5))
    matches: list[str] = []
    for _ in range(number):
        match = draw(st.text(alphabet=alphabet))
        assume(match not in matches)
        assume(match)
        matches.append(match)

    priorities = [draw(st.integers(min_value=0, max_value=20)) for _ in range(number)]

    models: dict[str, Arg[Any, Any]] = {}
    for i in range(len(matches)):
        id = f"{matches[i]}/{priorities[i]}"
        models[id] = Arg(
            id=id,
            priority=priorities[i],
            match=matchers.choice(matches[i]),
            format=lambda arg, *_: True,  # type: ignore
            default=False,
        )

    argv: list[str] = []
    tail: list[str] = []
    results = copy(models)
    for _ in range(draw(st.integers(min_value=0, max_value=number)) * 2):
        match, model = draw(st.sampled_from(list(zip(matches, models.values()))))
        argv.append(match)
        results[model.id] = model.with_value(match, Context([], 0, {}, None))

        extra_args = draw(st.integers(min_value=0, max_value=2))
        for _ in range(extra_args):
            extra = draw(st.text(alphabet=alphabet))
            assume(extra not in matches)
            argv.append(extra)
            tail.append(extra)

    return CliParams(argv, models, results, tail)


# def quick_arg(id):
#     return Arg(
#         id=id,
#         priority=10,
#         duplicates=DuplicatePolicy.REPLACE,
#         match=get_match_func(['0']),
#         format=bool,
#         num=1,
#     ).with_value("")
@given(cli_params())
def test_parser(params: CliParams):
    argv, models, results, tail = params
    a_result, a_tail = sc._match_args(argv, models, terminate_on_unknown=False)
    assert results == a_result
    assert tail == a_tail
