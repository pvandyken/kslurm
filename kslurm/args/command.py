from __future__ import absolute_import

import functools as ft
import inspect
import sys
from typing import Any, Callable, Literal, Optional, Union, overload

import attr

from kslurm.args.arg import Arg
from kslurm.args.arg_types import flag
from kslurm.args.helpers import finalize_model, get_arg_list
from kslurm.args.parser import ScriptHelp, parse_args
from kslurm.args.types import WrappedCommand
from kslurm.exceptions import CommandLineError

_CommandFunc = Callable[..., Optional[int]]
ModelType = Union[dict[str, Arg[Any, Any]], type]


ParsedArgs = dict[str, Arg[Any, Any]]


class CommandError(Exception):
    def __init__(self, msg: str, *args: Any):
        super().__init__(*args)
        self.msg = msg


class CommandArgs:
    _model: Optional[str] = None
    _tail: Optional[str] = None
    _modellist: Optional[str] = None
    _name: Optional[str] = None

    @property
    def model(self):
        return self._model

    @model.setter
    def model(self, value: str):
        if self._model is not None:
            raise ValueError("model is already set")
        self._model = value

    @property
    def tail(self):
        return self._tail

    @tail.setter
    def tail(self, value: str):
        if self._tail is not None:
            raise ValueError("tail is already set")
        self._tail = value

    @property
    def modellist(self):
        return self._modellist

    @modellist.setter
    def modellist(self, value: str):
        if self._modellist is not None:
            raise ValueError("modellist is already set")
        self._modellist = value

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value: str):
        if self._name is not None:
            raise ValueError("name is already set")
        self._name = value


@overload
def command(
    maybe_func: None = ...,
    *,
    terminate_on_unknown: bool = ...,
    typer: bool = ...,
) -> Callable[[_CommandFunc], WrappedCommand]:
    ...


@overload
def command(
    maybe_func: _CommandFunc = ...,
    *,
    terminate_on_unknown: Literal[True] = ...,
    typer: Literal[False] = ...,
) -> WrappedCommand:
    ...


def command(
    maybe_func: Optional[_CommandFunc] = None,
    *,
    terminate_on_unknown: bool = False,
    typer: bool = False,
) -> Union[WrappedCommand, Callable[[_CommandFunc], WrappedCommand]]:
    @attr.frozen
    class BlankModel:
        pass

    def decorator(func: _CommandFunc):
        if not callable(func):
            raise CommandLineError(f"{func} is not callable")

        params = inspect.signature(func)
        exceptions: Any = tuple()
        model = BlankModel

        command_args = CommandArgs()
        if typer:
            model = attr.make_class(
                "__Typer_Model__",
                {
                    param.name: attr.attrib(
                        default=param.default
                        if param.default is not params.empty
                        else attr.NOTHING,
                        type=param.annotation
                        if param.annotation is not params.empty
                        else attr.NOTHING,
                    )
                    for param in params.parameters.values()
                },
            )
        else:
            for param in params.parameters.values():
                if param.annotation == param.empty:
                    raise CommandLineError(
                        f"parameter '{param}' in {func} must be annotated"
                    )
                if param.annotation == list[str]:
                    command_args.tail = param.name
                    continue
                if param.annotation == ParsedArgs:
                    command_args.modellist = param.name
                    continue
                if param.annotation == str:
                    command_args.name = param.name
                    continue

                if model is not BlankModel:
                    raise CommandLineError(
                        f"Mutliple models detected: {model} and {param.annotation}"
                    )
                model = param.annotation
                if isinstance(model, str):
                    model = eval(model, func.__globals__)

                types = getattr(model, "__args__", None)
                if types is not None:
                    model = types[0]
                    exceptions = types[1:]

                if not attr.has(model):
                    raise CommandLineError(
                        f"Annotation of {param} in {func} must be an attr "
                        f"annotated class (currently {model})"
                    )
                command_args.model = param.name

        @ft.wraps(func)
        def wrapper(argv: list[str] = sys.argv):
            doc = func.__doc__
            if doc is None:
                doc = ""

            model_list = get_arg_list(model)
            model_list.append(flag(match=["--help", "-h"]).with_id("help"))
            try:
                if command_args.tail:
                    h = ScriptHelp(
                        script_name=argv[0], docstring=doc, usage_suffix="command_args"
                    )
                else:
                    h = ScriptHelp(script_name=argv[0], docstring=doc)
                parsed_list, tail = parse_args(
                    argv[1:],
                    model_list,
                    help=h,
                    terminate_on_unknown=terminate_on_unknown,
                )
                parsed_list = list(filter(lambda arg: arg.id != "help", parsed_list))
                parsed = finalize_model(parsed_list, model)
                if typer:
                    args = attr.asdict(parsed, recurse=False)
                else:
                    args = {
                        **(
                            {command_args.model: parsed}
                            if command_args.model is not None
                            else {}
                        ),
                        **(
                            {command_args.tail: tail}
                            if command_args.tail is not None
                            else {}
                        ),
                        **(
                            {
                                command_args.modellist: {
                                    arg.id: arg for arg in parsed_list
                                }
                            }
                            if command_args.modellist is not None
                            else {}
                        ),
                        **(
                            {command_args.name: argv[0]}
                            if command_args.name is not None
                            else {}
                        ),
                    }
            except exceptions as err:
                parsed = err
                args = {
                    **(
                        {command_args.model: parsed}
                        if command_args.model is not None
                        else {}
                    ),
                }
            try:
                return func(**args) or 0
            except CommandError as err:
                print(err.msg)
                return 1

        return wrapper

    if maybe_func is None:
        return decorator
    return decorator(maybe_func)
