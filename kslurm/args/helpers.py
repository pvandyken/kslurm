from __future__ import absolute_import, annotations

import itertools as it
import re
import typing
from collections import defaultdict
from typing import (
    Any,
    DefaultDict,
    Dict,
    Iterable,
    List,
    Literal,
    Optional,
    TypeVar,
    Union,
    cast,
    overload,
)

import attr
import docstring_parser as docparse
import more_itertools as itx

from kslurm.args import actions
from kslurm.args.arg import (
    Arg,
    Helpable,
    ParamInterface,
    ParamSet,
    Parser,
    SimpleParsable,
)
from kslurm.exceptions import CommandLineError

T = TypeVar("T")
S = TypeVar("S")
C = TypeVar("C", bound=Arg[Any])

ModelType = type[Any]
ModelDict = dict[str, ParamInterface[Any]]


def group_by_type(items: Iterable[T]) -> Dict[type, List[T]]:
    groupedDict = cast(DefaultDict[type, List[T]], defaultdict(list))
    for key, value in it.groupby(items, type):
        groupedDict[key] += list(value)
    return groupedDict


def get_parsers(models: ModelDict):
    result: dict[str, Parser[Any]] = {}
    for param in models.values():
        result.update(param.get_parsers())
    return result


@overload
def read_parsers(
    models: ModelDict,
    parsers: dict[str, Parser[Any]],
    raw_values: Literal[False] = ...,
    updated: Literal[False] = ...,
) -> tuple[dict[str, Any], dict[str, CommandLineError]]:
    ...


@overload
def read_parsers(
    models: ModelDict,
    parsers: dict[str, Parser[Any]],
    raw_values: Literal[True] = ...,
    updated: Literal[False] = ...,
) -> tuple[dict[str, Any], dict[str, CommandLineError], dict[str, list[str]]]:
    ...


@overload
def read_parsers(
    models: ModelDict,
    parsers: dict[str, Parser[Any]],
    raw_values: Literal[False] = ...,
    updated: Literal[True] = ...,
) -> tuple[dict[str, Any], dict[str, CommandLineError], dict[str, bool]]:
    ...


@overload
def read_parsers(
    models: ModelDict,
    parsers: dict[str, Parser[Any]],
    raw_values: Literal[True] = ...,
    updated: Literal[True] = ...,
) -> tuple[
    dict[str, Any], dict[str, CommandLineError], dict[str, list[str]], dict[str, bool]
]:
    ...


@overload
def read_parsers(
    models: ModelDict,
    parsers: dict[str, Parser[Any]],
    raw_values: bool = ...,
    updated: bool = ...,
) -> tuple[dict[str, Any], ...]:
    ...


def read_parsers(
    models: ModelDict,
    parsers: dict[str, Parser[Any]],
    raw_values: bool = False,
    updated: bool = False,
) -> Any:
    default: list[dict[str, Any]] = [{}, {}]
    if raw_values:
        default.append({})
    if updated:
        default.append({})
    unmerged = [
        model.read_parsers(parsers, raw_values, updated) for model in models.values()
    ]
    result = [_merge_dicts(elem) for elem in zip(*unmerged)]
    return tuple(result) or tuple(default)


@attr.frozen
class ParamAnnotation:
    is_optional: bool
    is_list: bool
    is_generic: bool
    main_type: type[Any]
    root_type: type[Any]

    @classmethod
    def parse(cls, __t: Optional[type[Any]], /):
        optional = False
        is_generic = False
        is_list = False
        if typing.get_origin(__t) == Union and type(None) in (
            args := typing.get_args(__t)
        ):
            i = args.index(type(None))
            rest = (*args[:i], *args[i + 1 :])
            if len(rest) > 1 or not len(rest):
                raise TypeError()
            optional = True
            __t = rest[0]
        main_type = __t
        if len(typing.get_args(__t)):
            is_generic = True
        if typing.get_origin(__t) == list:
            is_list = True
            __t = typing.get_args(__t)[0]
        if __t is None:
            __t = Literal[None]
        if main_type is None:
            main_type = Literal[None]
        return cls(
            is_optional=optional,
            is_generic=is_generic,
            is_list=is_list,
            main_type=main_type,
            root_type=__t,
        )


def _at_least(__iter: Iterable[T], __n: int, __default: T, /):
    i = 0
    for el in __iter:
        i += 1
        yield el
    yield from it.repeat(__default, max(__n - 1, 0))


def _parse_description(desc: str):
    x = [
        (match.group(1), match.group(2))
        if (match := re.match(r"@([\w\.]+)[ ]+(.*)?$", line))
        else (None, line)
        for line in filter(None, desc.splitlines())
    ]
    main, *_params = _at_least(itx.split_before(x, lambda _: _[0], maxsplit=1), 1, None)
    params = itx.first(_params, None)
    if params and itx.ilen(filter(lambda _: _[0] is None, params)):
        raise Exception()
    main = cast("list[tuple[None, str]] | None", main)
    params = cast("list[tuple[str, str]] | None", params)
    helptxt = " ".join([s[1] for s in main or []])
    meta: dict[str, Any] = {}
    for keypath, value in params or []:
        pointer = meta
        *keys, final = keypath.split(".")
        for key in keys:
            if key not in pointer:
                pointer[key] = {}
            pointer = pointer[key]
        pointer[final] = value
    return helptxt, meta


def get_arg_dict(models: ModelType) -> ModelDict:
    if not attr.has(models):
        raise TypeError(f"{type(models)} is not a supported object for arg models")

    doc = docparse.parse(models.__doc__ or "")
    arghelps = {arg.arg_name: arg for arg in doc.params}
    fields = attr.fields(models)
    result: ModelDict = {}
    for field in fields:
        if field.type is attr.NOTHING:
            raise TypeError(f"{field.name} must be annotated")

        annotation = ParamAnnotation.parse(field.type)

        # temporary assertion until we handle other defaults
        assert isinstance(field.default, SimpleParsable)

        default: SimpleParsable[Any] = field.default

        action = default.primary_parser.action
        if not action.has_formatter:
            newtype = annotation.root_type

            if annotation.is_list and not (
                isinstance(default, ParamSet) and isinstance(action, actions.append)
            ):
                raise TypeError(
                    f"invalid annotation for '{field.name}' in class "
                    f"'{models.__name__}': list annotations are not currently "
                    "supported in this context. Please provide a formatter to convert "
                    f"your arguments into lists (current annotation: '{field.type}')"
                )

            if not callable(newtype):
                raise TypeError(
                    f"{field.name} in '{models.__qualname__}' must be annotated with a "
                    "callable type"
                )

            default = default.with_primary_parser(
                attr.evolve(
                    default.primary_parser, action=action.with_converter(newtype)
                )
            )

        updates: dict[str, Any] = {"id": field.name}
        if isinstance(default, ParamSet) and default.default is attr.NOTHING:
            updates["default"] = annotation.root_type()

        if annotation.is_optional:
            updates["optional"] = True

        if field.name in arghelps:
            desc, meta = _parse_description(arghelps[field.name].description or "")
            if "name" in meta:
                updates["name"] = meta["name"]
            if isinstance(default, Helpable):
                updates["help"] = desc
                if default.help_template and "help" in meta:
                    try:
                        updates["help_template"] = default.help_template.update_meta(
                            **meta["help"]
                        )
                    except TypeError as err:
                        raise CommandLineError(
                            f"Unexpected param found when parsing {models} docstring, "
                            f"attribute '{field.name}': " + err.args[0]
                        )

        assert isinstance(default, ParamInterface)
        result[field.name] = attr.evolve(default, **updates)
    return result


def finalize_model(
    arg_updates: ModelDict, model: ModelType, exclude: list[str] = []
) -> Any:
    update = {
        arg.id: arg.value for arg in arg_updates.values() if arg.id not in exclude
    }
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


def _merge_dicts(dicts: Iterable[dict[T, S]]) -> dict[T, S]:
    result: dict[T, S] = {}
    for d in dicts:
        result.update(d)
    return result
