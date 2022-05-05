from __future__ import absolute_import

import itertools as it
from collections import defaultdict
from typing import Any, DefaultDict, Dict, Iterable, List, TypeVar, Union, cast

import attr

from kslurm.args.arg import Arg

T = TypeVar("T")
C = TypeVar("C", bound=Arg[Any, Any])

ModelType = Union[dict[str, Arg[Any, Any]], type]


def group_by_type(items: Iterable[T]) -> Dict[type, List[T]]:
    groupedDict = cast(DefaultDict[type, List[T]], defaultdict(list))
    for key, value in it.groupby(items, type):
        groupedDict[key] += list(value)
    return groupedDict


def get_arg_list(models: ModelType):
    if isinstance(models, dict):
        return [arg.with_id(name) for name, arg in models.items()]
    elif attr.has(models):
        fields = attr.fields(models)
        result: list[Arg[Any, Any]] = []
        for field in fields:
            if field.default is attr.NOTHING or not field.default:
                raise Exception()
            if field.type is attr.NOTHING:
                raise TypeError(f"{field.name} must be annotated")
            if field.default.num and not getattr(field.type, "__origin__") == list:
                raise TypeError(f"{field.name} must be annotated as a list")
            extra_args = {
                **(
                    {"format": field.type}
                    if field.default.format is str and not field.default.num
                    else {}
                ),
                **(
                    {"validate": getattr(field.type, "__args__")[0]}
                    if field.default.validate is str and field.default.num
                    else {}
                ),
            }
            result.append(attr.evolve(field.default, id=field.name, **extra_args))
        return result
    else:
        raise Exception(f"{type(models)} is not a supported object for arg models")


def update_model(
    arg_updates: Iterable[Arg[Any, Any]], model: ModelType
) -> list[Arg[Any, Any]]:
    update = {arg.id: arg for arg in arg_updates}
    if isinstance(model, dict):
        d = {**model, **update}
    elif attr.has(model):
        d = attr.asdict(model(**update), recurse=False)
    else:
        raise Exception(f"{type(model)} is not a supported object for arg models")
    return [arg.with_id(name) for name, arg in d.items()]


def finalize_model(arg_updates: Iterable[Arg[Any, Any]], model: ModelType) -> Any:
    update = {arg.id: (arg.values if arg.num else arg.value) for arg in arg_updates}
    if isinstance(model, dict):
        return cast(T, {**model, **update})
    elif attr.has(model):
        return model(**update)
    else:
        raise Exception(f"{type(model)} is not a supported object for arg models")


def get_help(model: Any) -> bool:
    if attr.has(model):
        help = getattr(model, "help", None)
        return getattr(help, "value", False)
    if isinstance(model, dict):
        help: Any = model.get("help", None)  # type: ignore
        return getattr(help, "value", False)
    raise Exception(f"{type(model)} is not a supported type for arg models")
