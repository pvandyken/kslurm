from __future__ import absolute_import

import itertools as it
from typing import (
    Any,
    Callable,
    Iterable,
    Iterator,
    List,
    Optional,
    TypeVar,
    Union,
    cast,
)

import kslurm.args.helpers as helpers
from kslurm.args.arg_sorter import ArgSorter
from kslurm.args.arg_types import Arg, KeywordArg, PositionalArg, TailArg
from kslurm.exceptions import (
    CommandLineError,
    CommandLineErrorGroup,
    MandatoryArgError,
    TailError,
)

T = TypeVar("T")
S = TypeVar("S")


def parse_args(args: Iterable[str], models: T, escalate_errors: bool = False) -> T:
    try:
        return _parse_args(args, models)
    except CommandLineError as err:
        print(err.msg)
        if isinstance(err, CommandLineErrorGroup):
            [print(e.msg) for e in err.sub_errors]
        if escalate_errors:
            raise err
        else:
            exit()


def _parse_args(args: Iterable[str], models: T) -> T:
    model_list = helpers.get_arg_list(models)

    sorted_models = ArgSorter(model_list)

    matchers = sorted_models.dynamic_args

    labelled = [_classify_arg(a, matchers) for a in args]
    grouped_args = list(
        _group_args(labelled, sorted_models.static_args, sorted_models.tail)
    )

    updated = helpers.update_model(grouped_args, models)

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
    return _group_arg(iter(args), 0, [], None, iter(positional_models), tail_model)


def _get_keyword_group_size(arg: Arg[Any]):
    if isinstance(arg, KeywordArg):
        return arg.num
    else:
        return 0


def _group_arg(
    input_args: Iterator[Arg[Any]],
    group_size: int,
    grouped_args: Iterable[Union[Arg[Any], None]],
    last_arg: Optional[Arg[Any]],
    positional_models: Iterator[PositionalArg[Any]],
    tail_model: Optional[TailArg],
) -> Iterable[Arg[Any]]:

    kcast: Callable[[Any], KeywordArg[Any]] = lambda x: cast(KeywordArg[Any], x)

    updated_args = it.chain(grouped_args, [last_arg])

    try:
        arg = next(input_args)
    except StopIteration:
        return filter(None, updated_args)

    if group_size:
        assert isinstance(last_arg, KeywordArg)
        new_arg = kcast(last_arg.add_values(it.chain(last_arg.values, [arg.raw_value])))
        new_group_size = group_size - 1
        updated_args = grouped_args

    elif all(
        [
            isinstance(last_arg, KeywordArg),
            _get_keyword_group_size(kcast(last_arg)) == 0,
            isinstance(arg, PositionalArg),
        ]
    ):
        # all() is not propagating the fact that last_arg is a keyword, so we assert it
        # here.
        assert isinstance(last_arg, KeywordArg)
        new_arg = kcast(last_arg.add_values(it.chain(last_arg.values, [arg.raw_value])))
        new_group_size = group_size
        updated_args = grouped_args

    elif isinstance(arg, PositionalArg):
        new_arg = _process_positional(
            cast(PositionalArg[Any], arg), positional_models, tail_model
        )
        new_group_size = _get_keyword_group_size(new_arg)

    else:
        new_arg = arg
        new_group_size = _get_keyword_group_size(new_arg)

    return _group_arg(
        input_args, new_group_size, updated_args, new_arg, positional_models, tail_model
    )


def _process_positional(
    arg: PositionalArg[Any],
    positional_models: Iterator[PositionalArg[Any]],
    tail_model: Optional[TailArg],
) -> Union[PositionalArg[Any], TailArg]:
    try:
        model = next(positional_models)
    except StopIteration:
        if tail_model:
            return tail_model.add_values([arg.raw_value])
        else:
            ret = TailArg().add_values([arg.raw_value])
            ret.raise_exception = True
            return ret
    return model.set_value(arg.raw_value)
