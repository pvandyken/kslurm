# pyright: reportPrivateUsage=false, reportUnknownArgumentType=false
from __future__ import absolute_import

from copy import copy
from typing import Any, NamedTuple

import hypothesis.strategies as st
from hypothesis import assume, given

import kslurm.args.parser as sc
from kslurm.args import actions, helpers, keyword, matchers
from kslurm.args.arg import Context, ParamInterface, Parser


class CliParsers(NamedTuple):
    argv: list[str]
    models: dict[str, Parser[Any]]
    results: dict[str, Parser[Any]]
    tail: list[str]


class CliParams(NamedTuple):
    argv: list[str]
    models: ParamInterface[Any]
    results: Any


class CliParamsZipped(NamedTuple):
    argv: tuple[list[str]]
    models: tuple[dict[str, ParamInterface[Any]]]
    results: tuple[dict[str, Any]]


@st.composite
def keyword_arg(draw: st.DrawFn, match_space: list[str] = []):
    alphabet = st.characters(blacklist_categories=("Cs", "Zs"))
    if not match_space:
        match = draw(st.text(alphabet, min_size=1))
    else:
        match = draw(st.sampled_from(match_space))
    entries = draw(
        st.lists(
            st.text(alphabet).filter(lambda s: s not in match_space),
            min_size=1,
            max_size=10,
        )
    )
    size = len(entries)
    argv = [match, *entries]
    models: ParamInterface[Any] = keyword(
        match=[match], default=None, num=size, id=match
    )

    return CliParams(argv, models, entries)


def arg():
    return st.text(st.characters(blacklist_categories=("Cs", "Zs")), min_size=1)


def match_space():
    return st.lists(arg(), min_size=5, max_size=20, unique=True)


@st.composite
def cli_params(draw: st.DrawFn):
    mspace = draw(match_space())

    priorities = draw(
        st.lists(
            st.integers(min_value=0, max_value=20), min_size=0, max_size=8, unique=True
        ),
    )

    matched: set[str] = set()
    models: dict[str, Parser[Any]] = {}
    argv: list[str] = []
    results = copy(models)
    tail: list[str] = []
    for i, p in enumerate(sorted(priorities, reverse=True)):
        matches = draw(
            st.lists(
                st.sampled_from(mspace),
                min_size=0,
                max_size=len(mspace),
                unique=True,
            )
        )

        id = f"{i}/{p} - ({matches})"
        models[id] = Parser(
            id=id,
            priority=p,
            match=matchers.choice(*matches),
            action=actions.replace(),
        )
        results[id] = models[id]
        unmatched = set(matches) - matched
        if unmatched:
            candidate = draw(st.sampled_from(list(unmatched)))
            argv.append(candidate)
            results[id] = models[id].with_value(candidate, Context([], 0, {}, None))
            matched.update(matches)

            # Add extra tail args
            for _ in range(draw(st.integers(min_value=0, max_value=2))):
                extra = draw(arg())
                assume(extra not in mspace)
                argv.append(extra)
                tail.append(extra)

    return CliParsers(argv, models, results, tail)


# @st.composite
# def keywords_and_flags(draw: st.DrawFn):
#     mspace = draw(match_space())
#     kwarg = draw(st.lists(keyword_arg()))
#     if len(kwarg) > 1:
#         argv, kw, results = cast(CliParamsZipped, zip(*kwarg))
#     return
#     number = draw(st.integers(min_value=0, max_value=5))
#     matches: list[str] = []
#     for _ in range(number):
#         match = draw(st.text(alphabet=alphabet))
#         assume(match not in matches)
#         assume(match)
#         matches.append(match)

#     num_args = [
#         draw(st.one_of(st.just(0), st.integers(min_value=0, max_value=5)))
#         for _ in range(number)
#     ]
#     priorities = [draw(st.integers(min_value=0, max_value=20)) for _ in range(number)]
#   greedinesses = [draw(st.integers(min_value=0, max_value=20)) for _ in range(number)]

#     model_list: list[Arg[Any, Any]] = []
#     for i in range(len(matches)):
#         id = f"{matches[i]}/{priorities[i]}"
#         model = Arg(
#             id=id,
#             priority=priorities[i],
#             match=matchers.choice(matches[i]),
#             format=lambda arg, *_: True,  # type: ignore
#             default=False,
#         )
#         model_list.append(model)

#     models: dict[str, Arg[Any, Any]] = {}
#     for i in range(len(matches)):
#         id = model_list[i].id
#         models[id] = model_list[i]
#         if num_args[i]:
#             models[id + " (args)"] = Arg(
#                 id=id + " (args)",
#                 priority=greedinesses[i],
#                 match=matchers.option_chain(id, num_args[i], matchers.everything()),
#                 format=lambda arg, *_: arg,  # type: ignore
#             )

#     argv: list[str] = []
#     tail: list[str] = []
#     results = copy(models)
#     prev_priority = 0
#     for _ in range(draw(st.integers(min_value=0, max_value=number)) * 2):
#         higher_priority = [
#             match for i, match in enumerate(matches) if priorities[i] >= prev_priority
#         ]
#         if not len(higher_priority):
#             break
#         index = matches.index(draw(st.sampled_from(higher_priority)))
#         argv.append(matches[index])
#         num_params = draw(st.integers(min_value=0, max_value=num_args[index]))
#         params: list[str] = []
#         for _ in range(num_params):
#             lower_priority = [
#                 match
#                 for i, match in enumerate(matches)
#                 if priorities[i] < greedinesses[index]
#             ]
#             higher_priority = [
#                 match for match in matches if match not in lower_priority
#             ]
#             if len(lower_priority):
#                 param = draw(
#                     st.one_of(
#                         st.text(alphabet=alphabet), st.sampled_from(lower_priority)
#                     )
#                 )
#             else:
#                 param = draw(st.text(alphabet=alphabet))
#             assume(param not in higher_priority)
#             params.append(param)
#         prev_priority = greedinesses[index]
#         argv.extend(params)
#         id = model_list[index].id
#         results[id] = attrs.evolve(models[id], value=True)
#         results[id + " (args)"] = attrs.evolve(results[id + " (args)"], value=params)

#         if num_params == num_args[index]:
#             extra_args = draw(st.integers(min_value=0, max_value=2))
#             for _ in range(extra_args):
#                 extra = draw(st.text(alphabet=alphabet))
#                 assume(extra not in matches)
#                 argv.append(extra)
#                 tail.append(extra)

#     return CliParams(argv, models, results, tail)


@given(keyword_arg())
def test_keyword_arg(params: CliParams):
    argv, models, template = params
    parsers = helpers.get_parsers({models.id: models})
    parsed, tail = sc.parse_args(argv, parsers)
    print(parsed)
    results, err = helpers.read_parsers({models.id: models}, parsed)
    assert err == {}
    assert results == {models.id: template}
    assert tail == []


@given(cli_params())
def test_parser(params: CliParsers):
    argv, models, results, tail = params
    a_result, a_tail = sc._match_args(argv, models, terminate_on_unknown=False)
    assert results == a_result
    assert tail == a_tail
