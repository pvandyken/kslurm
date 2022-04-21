from __future__ import absolute_import, annotations

import itertools as it
from typing import (
    Any,
    Callable,
    Iterable,
    Iterator,
    List,
    Optional,
    Tuple,
    TypeVar,
    Union,
    cast,
)

import kslurm.args.helpers as helpers
from kslurm.args.arg_sorter import ArgSorter
from kslurm.args.arg_types import Arg, FlagArg, KeywordArg, PositionalArg, TailArg
from kslurm.args.help import print_help
from kslurm.exceptions import (
    CommandLineError,
    CommandLineErrorGroup,
    MandatoryArgError,
    TailError,
)

T = TypeVar("T")
S = TypeVar("S")


def parse_args(
    args: Iterable[str],
    models: T,
    escalate_errors: bool = False,
    script_name: str = "",
    docstring: str = "",
) -> T:
    try:
        return _parse_args(args, models, script_name, docstring)
    except CommandLineError as err:
        print(err.msg)
        if isinstance(err, CommandLineErrorGroup):
            [print(e.msg) for e in err.sub_errors]
        if escalate_errors:
            raise err
        else:
            exit()


def _parse_args(args: Iterable[str], models: T, script_name: str, docstring: str) -> T:
    model_list = helpers.get_arg_list(models)
    model_list.append(FlagArg(id="help", match=["--help", "-h"]))

    sorted_models = ArgSorter(model_list)

    matchers = sorted_models.dynamic_args

    labelled = [_classify_arg(a, matchers) for a in args]
    grouped_args = list(
        _group_args(labelled, sorted_models.static_args, sorted_models.tail)
    )

    show_help = False
    for arg in grouped_args:
        if arg.id == "help":
            show_help = arg.value
            break

    updated = helpers.update_model(
        filter(lambda arg: arg.id != "help", grouped_args), models
    )

    if show_help:
        print_help(script_name, models, docstring)
        exit(0)

    sorted_args = ArgSorter(helpers.get_arg_list(updated))

    validation_errs = filter(
        None, [arg.validation_err for arg in sorted_args.validated_args]
    )

    tail_arg = sorted_args.tail
    if tail_arg and tail_arg.raise_exception:
        tail_err = [
            TailError(
                f"{tail_arg.values} does not match any Shape, Keyword, or Positional "
                "Args."
            )
        ]
    else:
        tail_err = []

    mandatory_arg_errs = cast(List[MandatoryArgError], [])
    for arg in helpers.get_arg_list(updated):
        try:
            arg.value
        except MandatoryArgError as err:
            mandatory_arg_errs.append(err)

    all_err = list(it.chain(validation_errs, tail_err, mandatory_arg_errs))

    if all_err:
        raise CommandLineErrorGroup("Problems found!", all_err)

    return updated


def _classify_arg(arg: str, arg_list: Iterable[Arg[Any]]):
    for argtype in arg_list:
        if argtype.match(arg):
            return argtype.set_value(arg)
    return cast(Arg[Any], PositionalArg().set_value(arg))


def _group_args(
    args: List[Arg[Any]],
    positional_models: Iterable[PositionalArg[Any]],
    tail_model: Optional[TailArg],
) -> Iterable[Arg[Any]]:

    group_size: int = 0
    prev_arg: Optional[Arg[Any]] = None
    positional_iter: Iterator[PositionalArg[Any]] = iter(positional_models)
    terminated = False

    updated_args: Iterable[Optional[Arg[Any]]] = []
    next_update = updated_args

    kcast: Callable[[Any], KeywordArg[Any]] = lambda x: cast(KeywordArg[Any], x)
    for arg in args:
        # Pyright is stupid and adds Keyword[Unknown] as a type annotation following
        # isinstance(_, KeywordArg). This messes up all the following code so we make a
        # a new variable to bear the burden of the unnecessary annotation and avoid
        # lots of casting
        prev_kw = prev_arg
        if (
            group_size
            and isinstance(prev_kw, KeywordArg)
            and (isinstance(arg, PositionalArg) or not prev_kw.lazy)
        ):
            prev_arg = kcast(
                prev_kw.add_values(it.chain(prev_kw.values, [arg.raw_value]))
            )
            group_size -= 1
            next_update = it.chain(updated_args, [prev_arg])
            continue

        updated_args = next_update

        if terminated:
            prev_arg, tail_model = _process_tail(arg, tail_model, True)
            group_size = _get_keyword_group_size(prev_arg)

        elif isinstance(arg, PositionalArg):
            new_arg, tail_model = _process_positional(arg, positional_iter, tail_model)
            if new_arg is None:
                new_arg = prev_arg
            group_size = _get_keyword_group_size(new_arg)
            prev_arg = new_arg

        else:
            group_size = _get_keyword_group_size(arg)
            prev_arg = arg

        if prev_arg and prev_arg.terminal:
            terminated = True

        next_update = it.chain(updated_args, [prev_arg])

    updated_args = next_update

    return list(filter(None, updated_args))


def _get_keyword_group_size(arg: Optional[Arg[Any]]):
    if isinstance(arg, KeywordArg):
        return arg.num
    else:
        return 0


def _process_positional(
    arg: PositionalArg[Any],
    positional_models: Iterator[PositionalArg[Any]],
    tail_model: Optional[TailArg],
    terminate: bool = True,
) -> Tuple[Union[PositionalArg[Any], TailArg, None], Optional[TailArg]]:
    try:
        model = next(positional_models)
    except StopIteration:
        return _process_tail(arg, tail_model, terminate)
    return model.set_value(arg.raw_value), tail_model


def _process_tail(
    arg: Arg[Any], tail_model: Optional[TailArg], terminate: bool = False
):
    if tail_model:
        new_tail = tail_model.add_values([arg.raw_value])
    else:
        ret = TailArg().add_values([arg.raw_value])
        ret.raise_exception = True
        new_tail = ret

    if terminate:
        return new_tail, None
    return None, new_tail
