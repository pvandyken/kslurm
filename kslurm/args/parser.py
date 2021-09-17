from kslurm.exceptions import CommandLineError
from typing import Any, Callable, List, TypeVar, cast, Iterable, Tuple

import functools as fc
import itertools as it

import kslurm.args.helpers as helpers
from .arg_types import Arg, FlagArg, ShapeArg, KeywordArg, PositionalArg, TailArg

T = TypeVar("T")
S = TypeVar("S")

def parse_args(args: Iterable[str], models: T) -> T:
    try:
        return _parse_args(args, models)
    except CommandLineError as err:
        print(err.msg)
        exit()

def _parse_args(args: Iterable[str], models: T) -> T:
    model_list = helpers.get_arg_list(models)

    model_cats = helpers.group_by_type(model_list)

    specific_args = list(it.chain(
        model_cats.get(ShapeArg, []),
        model_cats.get(KeywordArg, []),
        model_cats.get(FlagArg, [])
    ))
    
    labelled = [classify_arg(a, specific_args) for a in args]
    grouped = helpers.group_by_type(group_keywords(labelled))
    shape_args = grouped.get(ShapeArg, [])
    keyword_args = grouped.get(KeywordArg, [])
    flag_args = grouped.get(FlagArg, [])

    nonspecific_args = cast(
        Iterable[PositionalArg[Any]], 
        grouped.get(PositionalArg, [])
    )

    positional_models = cast(
        Iterable[PositionalArg[Any]],
        filter(lambda x: isinstance(x, PositionalArg), model_list)
    )
    positional_args, extras = delineate_positional(nonspecific_args, positional_models)

    if TailArg in model_cats:
        tail_arg_list = cast(List[TailArg], list(model_cats[TailArg]))
        if len(tail_arg_list) > 1:
            raise CommandLineError("More than 1 TailArgs provided:"
                            f"{tail_arg_list}")
        
        tail_arg = tail_arg_list[0]
        tail = [tail_arg.add_values([v.raw_value for v in extras])]
    else:
        tail = cast(List[TailArg], [])
        if extras:
            raise CommandLineError(f"{extras} does not match any Shape, Keyword, or Positional Args ")
    
    return helpers.update_model(it.chain(shape_args, positional_args, keyword_args, flag_args, tail), models)

def classify_arg(arg: str, arg_list: Iterable[Arg[Any]]):
    for argtype in arg_list:
        if argtype.match(arg):
            return argtype.set_value(arg)
    return cast(Arg[Any], PositionalArg().set_value(arg))


def group_keywords(args: List[Arg[Any]]) -> Iterable[Arg[Any]]:
    return fc.reduce(
        group_keyword, 
        args, 
        ( 0, cast(List[Arg[Any]], []) )
    )[1]
    

def get_keyword_group_size(arg: Arg[Any]):
    if isinstance(arg, KeywordArg):
        return arg.num
    else:
        return 0

def group_keyword(accumulant: Tuple[int, Iterable[Arg[Any]]], arg: Arg[Any]) -> "Tuple[int, Iterable[Arg[Any]]]":
    group_size, running_list = accumulant
    new_keyword_group_size = get_keyword_group_size(arg)

    kcast: Callable[[Any], KeywordArg[Any]] = lambda x: cast(KeywordArg[Any], x)
    l = list(running_list)
    if l:
        last_arg = l[-1]
    else:
        last_arg = None
   
    if group_size:
        assert isinstance(last_arg, KeywordArg)
        kcast(last_arg)
        return (
            group_size - 1, 
            it.chain(
                l[:-1], 
                [kcast(last_arg.add_values(it.chain(
                    last_arg.values,
                    [arg.raw_value]
                )))]
            )
        )
    elif isinstance(last_arg, KeywordArg) and \
        get_keyword_group_size(kcast(last_arg)) == 0 and \
        not isinstance(arg, ShapeArg) and \
        not isinstance(arg, KeywordArg):
        return (
            group_size, 
            it.chain(
                l[:-1], 
                [kcast(last_arg.add_values(it.chain(
                    last_arg.values,
                    [arg.raw_value]
                )))] 
            )
        )
    else:
        return new_keyword_group_size, it.chain(l, [cast(Arg[Any], arg)]) 


def delineate_positional(args: Iterable[PositionalArg[Any]], positional_models: Iterable[PositionalArg[Any]]) -> Tuple[List[PositionalArg[Any]], List[PositionalArg[Any]]]:
    args = list(args)
    models = list(positional_models)
    if len(args) < len(models):
        raise CommandLineError("Too few positional arguments received.\n"
                        f"Expected {models}\n"
                        f"but got {args}")
    
    positional_args = [
        model.set_value(arg.raw_value)
        for arg, model in zip(args, models)
    ]
    
    # We return all the args not zipped with the models as
    # extras to be added to TailArg
    return positional_args, args[len(models):]