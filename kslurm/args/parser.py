from __future__ import absolute_import, annotations

import itertools as it
from typing import Any, Iterable, List, Optional, TypeVar, Union

from kslurm.args.arg import Arg, DuplicatePolicy
from kslurm.exceptions import (
    CommandLineErrorGroup,
    MandatoryArgError,
    TailError,
    ValidationError,
)

T = TypeVar("T", bound=Union[dict[str, Arg[Any, Any]], type])
S = TypeVar("S")


def parse_args(
    args: Iterable[str],
    models: list[Arg[Any, Any]],
    allow_unknown: bool = True,
    terminate_on_unknown: bool = True,
):
    model_list = sorted(models, key=lambda arg: arg.priority, reverse=True)

    parsed, tail = _match_args(args, model_list, terminate_on_unknown)

    validation_errs = filter(None, [arg.validation_err for arg in parsed])

    if tail and not allow_unknown:
        tail_err = [TailError(f"{tail} does not match any args")]
    else:
        tail_err = []

    mandatory_arg_errs: list[MandatoryArgError] = []
    for arg in parsed:
        try:
            arg.value
        except MandatoryArgError as err:
            if arg.validation_err is None:
                mandatory_arg_errs.append(err)

    all_err = list(it.chain(validation_errs, tail_err, mandatory_arg_errs))

    if all_err:
        raise CommandLineErrorGroup("Multiple errors found", all_err)

    return parsed, tail


def _match_args(
    args: Iterable[str],
    arg_list: List[Arg[Any, Any]],
    terminate_on_unknown: bool = True,
):

    group_size: int = 0
    prev_arg: Optional[Arg[Any, Any]] = None
    terminated = False

    updated_args: Iterable[Optional[Arg[Any, Any]]] = []
    next_update = updated_args

    skip: list[Arg[Any, Any]] = list()
    matched: list[Arg[Any, Any]] = list()
    tail: list[str] = []

    for arg in args:
        if terminated:
            tail.append(arg)
            continue

        next_arg = None
        sub_arg: Optional[Arg[Any, None]] = None
        for argtype in arg_list:
            sub_arg_match = sub_arg is not None and sub_arg.match(arg)
            if argtype.match(arg) and argtype not in skip:
                if sub_arg_match and sub_arg.priority > argtype.priority:
                    try:
                        sub_arg = sub_arg.with_value(arg)
                    except ValidationError as err:
                        sub_arg = sub_arg.with_err(err)
                    group_size -= 1
                    next_update = it.chain(updated_args, [next_arg])
                    break
                updated_args = next_update
                try:
                    next_arg = argtype.with_value(arg, True)
                except ValidationError as err:
                    next_arg = argtype.with_err(err)
                sub_arg = argtype.sub_arg
                if argtype.terminal:
                    terminated = True
                if next_arg.duplicates == DuplicatePolicy.SKIP:
                    skip.append(argtype)
                matched.append(argtype)
                next_update = it.chain(updated_args, [next_arg])
                break
        if next_arg is None:
            if prev_arg and group_size:
                try:
                    next_arg = prev_arg.with_values(
                        it.chain(prev_arg.values, [arg]), True
                    )
                except ValidationError as err:
                    next_arg = prev_arg.with_err(err)
                group_size -= 1
                next_update = it.chain(updated_args, [next_arg])
            else:
                tail.append(arg)
                if terminate_on_unknown:
                    terminated = True

        if next_arg is not None:
            prev_arg = next_arg

    unchanged = [arg for arg in arg_list if arg not in matched]

    updated_args = it.chain(next_update, unchanged)

    return list(filter(None, updated_args)), tail
