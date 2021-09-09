from collections import defaultdict
from typing import DefaultDict, Dict, ItemsView, List, TypeVar, cast, Iterable, Tuple

import attr
import cluster_utils.args.arg_types as arglib
from cluster_utils.args.arg_types import Arg, ShapeArg, KeywordArg, PositionalArg, TailArg
import functools as fc
import itertools as it

T = TypeVar("T")

def relabel_args(models: object):
    if hasattr(models, "__attrs_attrs__"):
        return [
            cast(Arg, arg.setid(name)) for name, arg in attr.asdict(models, recurse=False).items()
        ]
    elif isinstance(models, dict):
        return [
            arg.setid(name) for name, arg in cast(ItemsView[str, arglib.Arg], models.items() )
        ]
    else:
        raise Exception(f"{type(models)} is not a supported object for arg models")

def group_by_type(items: Iterable[T]) -> Dict[type, List[T]]:
    groupedDict = cast(DefaultDict[type, List[T]], defaultdict(list))
    for key, value in it.groupby(items, type):
        groupedDict[key] += list(value)
    return groupedDict

def update_model(arg_updates: Iterable[arglib.Arg], model: T) -> T:
    update = { 
        arg.id: arg for arg in arg_updates
    }
    return model.__class__(**update)


def parse_args(args: Iterable[str], models: T) -> T:
    model_list = relabel_args(models)

    model_cats = group_by_type(model_list)

    specific_args = list(it.chain(
        model_cats.get(ShapeArg, []),
        model_cats.get(KeywordArg, [])
    ))
    
    labelled = [classify_arg(a, specific_args) for a in args]
    grouped = group_by_type(group_keywords(labelled))
    shape_args = grouped.get(ShapeArg, [])
    keyword_args = grouped.get(KeywordArg, [])

    nonspecific_args = cast(
        Iterable[PositionalArg], 
        grouped.get(PositionalArg, [])
    )
    positional_models = cast(
        Iterable[PositionalArg], 
        model_cats.get(PositionalArg, [])
    )
    positional_args, extras = delineate_positional(nonspecific_args, positional_models)

    if TailArg in model_cats:
        tail_arg_list = cast(List[TailArg], list(model_cats[TailArg]))
        if len(tail_arg_list) > 1:
            raise Exception("More than 1 TailArgs provided:"
                            f"{tail_arg_list}")
        
        tail_arg = tail_arg_list[0]
        tail = [tail_arg.add_values([v.value for v in extras])]
    else:
        tail = cast(List[TailArg], [])
        if extras:
            raise Exception(f"{extras} are not valid arguments. Please add a TailArg to your "
                                "model to collect extra arguments")
    
    return update_model(it.chain(shape_args, positional_args, keyword_args, tail), models)

def classify_arg(arg: str, arg_list: Iterable[arglib.Arg]):
    for argtype in arg_list:
        if argtype.match(arg):
            return argtype.set_value(arg)
    return cast(Arg, PositionalArg().set_value(arg))


def group_keywords(args: List[arglib.Arg]) -> Iterable[arglib.Arg]:
    return fc.reduce(
        group_keyword, 
        args, 
        ( 0, cast(List[Arg], []) )
    )[1]
    

def get_keyword_group_size(arg: arglib.Arg):
    if isinstance(arg, arglib.KeywordArg):
        return arg.num
    else:
        return 0

def group_keyword(accumulant: Tuple[int, Iterable[Arg]], arg: Arg) -> Tuple[int, Iterable[Arg]]:
    group_size, running_list = accumulant
    new_keyword_group_size = get_keyword_group_size(arg)

    l = list(running_list)
    if l:
        last_arg = l[-1]
    else:
        last_arg = None
   
    if group_size:
        assert isinstance(last_arg, KeywordArg)
        return (
            group_size - 1, 
            it.chain(
                l[:-1], 
                [last_arg.add_values(it.chain(
                    last_arg.values,
                    [arg.value]
                ))]
            )
        )
    elif isinstance(last_arg, KeywordArg) and \
        get_keyword_group_size(last_arg) == 0 and \
        not isinstance(arg, ShapeArg) and \
        not isinstance(arg, KeywordArg):
        return (
            group_size, 
            it.chain(
                l[:-1], 
                [last_arg.add_values(it.chain(
                    last_arg.values,
                    [arg.value]
                ))]
            )
        )
    else:
        assert isinstance(arg, Arg)
        return new_keyword_group_size, it.chain(l, [arg])


def delineate_positional(args: Iterable[PositionalArg], positional_models: Iterable[PositionalArg]) -> Tuple[List[PositionalArg], List[PositionalArg]]:
    args = list(args)
    models = list(positional_models)
    if len(args) < len(models):
        raise Exception("Two few positional arguments received.\n"
                        f"Expected {models}\n"
                        f"but got {args}")
    
    positional_args = [
        model.set_value(arg.value)
        for arg, model in zip(args, models)
    ]
    
    # We return all the args not zipped with the models as
    # extras to be added to TailArg
    return positional_args, args[len(models):]