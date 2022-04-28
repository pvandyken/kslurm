# pyright: reportPrivateUsage=false, reportUnknownArgumentType=false
from __future__ import absolute_import

from typing import Any, NamedTuple

import hypothesis.strategies as st
from hypothesis import assume, given

import kslurm.args.parser as sc
from kslurm.args.arg import Arg, DuplicatePolicy


def get_match_func(match_list: list[str]):
    def match_func(arg: str):
        return arg in match_list

    return match_func


CliParams = NamedTuple(
    "CliParams",
    [
        ("argv", list[str]),
        ("models", list[Arg[Any, Any]]),
        ("results", list[Arg[Any, Any]]),
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

    num_args = [
        draw(st.one_of(st.just(0), st.integers(min_value=0, max_value=5)))
        for _ in range(number)
    ]
    priorities = [draw(st.integers(min_value=0, max_value=20)) for _ in range(number)]
    greedinesses = [draw(st.integers(min_value=0, max_value=20)) for _ in range(number)]

    models: list[Arg[Any, Any]] = []
    for i in range(len(matches)):
        model: Arg[Any, Any] = Arg(
            id=f"{matches[i]}/{priorities[i]} (+{num_args[i]}/{greedinesses[i]})",
            priority=priorities[i],
            greediness=greedinesses[i],
            duplicates=DuplicatePolicy.REPLACE,
            match=get_match_func([matches[i]]),
            format=bool,
            num=num_args[i],
        ).with_value("")
        models.append(model)

    used: list[bool] = [False] * number
    argv: list[str] = []
    tail: list[str] = []
    results: list[Arg[Any, Any]] = []
    prev_priority = 0
    for _ in range(draw(st.integers(min_value=0, max_value=number)) * 2):
        higher_priority = [
            match for i, match in enumerate(matches) if priorities[i] >= prev_priority
        ]
        if not len(higher_priority):
            break
        index = matches.index(draw(st.sampled_from(higher_priority)))
        argv.append(matches[index])
        used[index] = True
        num_params = draw(st.integers(min_value=0, max_value=num_args[index]))
        params: list[str] = []
        for _ in range(num_params):
            lower_priority = [
                match
                for i, match in enumerate(matches)
                if priorities[i] < greedinesses[index]
            ]
            higher_priority = [
                match for match in matches if match not in lower_priority
            ]
            if len(lower_priority):
                param = draw(
                    st.one_of(
                        st.text(alphabet=alphabet), st.sampled_from(lower_priority)
                    )
                )
            else:
                param = draw(st.text(alphabet=alphabet))
            assume(param not in higher_priority)
            params.append(param)
        prev_priority = greedinesses[index]
        argv.extend(params)
        results.append(models[index].with_value(matches[index]).with_values(params))

        if num_params == num_args[index]:
            extra_args = draw(st.integers(min_value=0, max_value=2))
            for _ in range(extra_args):
                extra = draw(st.text(alphabet=alphabet))
                assume(extra not in matches)
                argv.append(extra)
                tail.append(extra)

    for i, u in enumerate(used):
        if not u:
            results.append(models[i])

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
