from __future__ import absolute_import, annotations

import itertools as it
from typing import Any, Iterable, List, Optional, TypeVar, Union, cast

import attr

from kslurm.args.arg import Arg, DuplicatePolicy
from kslurm.args.help import print_help
from kslurm.exceptions import (
    CommandLineError,
    CommandLineErrorGroup,
    MandatoryArgError,
    TailError,
    ValidationError,
)

T = TypeVar("T", bound=Union[dict[str, Arg[Any, Any]], type])
S = TypeVar("S")


@attr.frozen
class ScriptHelp:
    script_name: str = ""
    docstring: str = ""
    usage_suffix: str = ""


def parse_args(
    args: Iterable[str],
    models: list[Arg[Any, Any]],
    escalate_errors: bool = False,
    help: ScriptHelp = ScriptHelp(),
    allow_unknown: bool = True,
    terminate_on_unknown: bool = True,
):
    try:
        return _parse_args(
            args,
            models,
            help,
            allow_unknown=allow_unknown,
            terminate_on_unknown=terminate_on_unknown,
        )
    except CommandLineError as err:
        print(err.msg)
        if isinstance(err, CommandLineErrorGroup):
            [print(e.msg) for e in err.sub_errors]
        if escalate_errors:
            raise err
        else:
            exit()


def _parse_args(
    args: Iterable[str],
    models: list[Arg[Any, Any]],
    help: ScriptHelp,
    allow_unknown: bool = True,
    terminate_on_unknown: bool = True,
):
    model_list = sorted(models, key=lambda arg: arg.priority, reverse=True)

    parsed, tail = _match_args(args, model_list, terminate_on_unknown)

    show_help = False
    for arg in parsed:
        if arg.id == "help":
            show_help = arg.value
            break

    if show_help:
        print_help(help.script_name, models, help.docstring, help.usage_suffix)
        exit(0)

    validation_errs = filter(None, [arg.validation_err for arg in parsed])

    if tail and not allow_unknown:
        tail_err = [TailError(f"{tail} does not match any args")]
    else:
        tail_err = []

    mandatory_arg_errs = cast(List[MandatoryArgError], [])
    for arg in parsed:
        try:
            arg.value
        except MandatoryArgError as err:
            mandatory_arg_errs.append(err)

    all_err = list(it.chain(validation_errs, tail_err, mandatory_arg_errs))

    if all_err:
        raise CommandLineErrorGroup("Problems found!", all_err)

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
        for argtype in arg_list:
            if argtype.match(arg) and argtype not in skip:
                if prev_arg and group_size and prev_arg.greediness > argtype.priority:
                    try:
                        next_arg = prev_arg.with_values(
                            it.chain(prev_arg.values, [arg]), True
                        )
                    except ValidationError as err:
                        next_arg = prev_arg.with_err(err)
                    group_size -= 1
                    next_update = it.chain(updated_args, [next_arg])
                    break
                updated_args = next_update
                try:
                    next_arg = argtype.with_value(arg, True)
                except ValidationError as err:
                    next_arg = argtype.with_err(err)
                group_size = argtype.num
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
