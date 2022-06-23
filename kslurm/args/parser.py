from __future__ import absolute_import, annotations

from copy import copy
from typing import Any, Iterable, TypeVar, Union

from kslurm.args.arg import Arg, Context, Parser
from kslurm.exceptions import TailError

T = TypeVar("T", bound=Union[dict[str, Arg[Any]], type])
S = TypeVar("S")


def parse_args(
    args: Iterable[str],
    models: dict[str, Parser[Any]],
    allow_unknown: bool = True,
    terminate_on_unknown: bool = True,
):

    parsed, tail = _match_args(args, models, terminate_on_unknown)

    if tail and not allow_unknown:
        tail = TailError(f"{tail} does not match any args")

    return parsed, tail


def _match_args(
    args: Iterable[str],
    parsers: dict[str, Parser[Any]],
    terminate_on_unknown: bool = True,
):

    updated_params = copy(parsers)
    terminated = False

    tail: list[str] = []

    sorted_params = [
        parser.id
        for parser in sorted(
            parsers.values(), key=lambda param: param.priority, reverse=True
        )
    ]
    arg_list = list(args)
    last_match = None
    for i, arg in enumerate(arg_list):
        if terminated:
            tail.append(arg)
            continue
        next_fragment = arg
        while isinstance(next_fragment, str):
            fragment: str = next_fragment

            context = Context(
                args=arg_list,
                current_arg=i,
                params=updated_params,
                last_matched=last_match,
            )
            matched_arg = False
            for id in sorted_params:
                parser = updated_params[id]
                if next_fragment := parser.match(fragment, parser, context):
                    updated_params[id] = parser.with_value(fragment, context)
                    if parser.terminal:
                        terminated = True
                    last_match = updated_params[parser.id]
                    matched_arg = True
                    break
            if not matched_arg:
                next_fragment = False
                tail.append(arg)
                if terminate_on_unknown:
                    terminated = True

    return updated_params, tail
