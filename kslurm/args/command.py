from __future__ import absolute_import

import functools as ft
import inspect
import sys
from typing import Any, Callable, Literal, Optional, Union, overload

import attr
from typing_extensions import ParamSpec

from kslurm.args.arg import Arg
from kslurm.args.arg_types import HelpRequest, help_arg
from kslurm.args.help import print_help
from kslurm.args.helpers import finalize_model, get_arg_list
from kslurm.args.parser import parse_args
from kslurm.args.protocols import TransparentWrappedCommand, WrappedCommand
from kslurm.exceptions import CommandLineError, CommandLineErrorGroup

P = ParamSpec("P")
_CommandFunc = Callable[P, Optional[int]]
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
    inline: Literal[False] = ...,
) -> Callable[[_CommandFunc[P]], WrappedCommand]:
    ...


@overload
def command(
    maybe_func: None = ...,
    *,
    terminate_on_unknown: bool = ...,
    inline: Literal[True] = ...,
) -> Callable[[_CommandFunc[P]], TransparentWrappedCommand[P]]:
    ...


@overload
def command(
    maybe_func: _CommandFunc[P] = ...,
    *,
    terminate_on_unknown: Literal[True] = ...,
    inline: Literal[False] = ...,
) -> WrappedCommand:
    ...


def command(
    maybe_func: Optional[_CommandFunc[P]] = None,
    *,
    terminate_on_unknown: bool = False,
    inline: bool = False,
) -> Union[
    WrappedCommand,
    Callable[[_CommandFunc[P]], WrappedCommand],
    Callable[[_CommandFunc[P]], Callable[P, int]],
]:
    @attr.frozen
    class BlankModel:
        pass

    def decorator(func: _CommandFunc[P]):
        if not callable(func):
            raise CommandLineError(f"{func} is not callable")

        params = inspect.signature(func)
        exceptions: Any = tuple()
        model = BlankModel

        command_args = CommandArgs()
        if inline:
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

        def wrapper(argv: list[str] = sys.argv):
            doc = func.__doc__
            if doc is None:
                doc = ""

            model_list = get_arg_list(model)
            if command_args.tail:
                usage_suffix = "command_args"
            else:
                usage_suffix = ""
            try:
                parsed_list, tail = parse_args(
                    argv[1:],
                    model_list + [help_arg().with_id("help")],
                    terminate_on_unknown=terminate_on_unknown,
                )

                parsed = finalize_model(parsed_list, model, exclude=["help"])
                if inline:
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
            except (HelpRequest, CommandLineError, *exceptions) as err:
                in_exceptions = isinstance(err, exceptions)
                if isinstance(err, CommandLineError) and not in_exceptions:
                    print_help(argv[0], model_list, doc, usage_suffix, just_usage=True)
                    if isinstance(err, CommandLineErrorGroup):
                        [print(e.msg) for e in err.sub_errors]
                    else:
                        print(err.msg)
                    return 1
                if isinstance(err, HelpRequest) and not in_exceptions:
                    print_help(argv[0], model_list, doc, usage_suffix)
                    return 0

                parsed = err
                args: dict[str, Any] = {
                    **(
                        {command_args.model: parsed}
                        if command_args.model is not None
                        else {}
                    ),
                    **(
                        {command_args.tail: []} if command_args.tail is not None else {}
                    ),
                    **(
                        {command_args.modellist: {}}
                        if command_args.modellist is not None
                        else {}
                    ),
                    **(
                        {command_args.name: argv[0]}
                        if command_args.name is not None
                        else {}
                    ),
                }

            try:
                return func(**args) or 0  # type: ignore
            except CommandError as err:
                print(err.msg)
                return 1

        @overload
        def disambiguator(*args: P.args, **kwargs: P.kwargs) -> int:
            ...

        @overload
        def disambiguator(argv: list[str] = ...) -> int:
            ...

        @ft.wraps(func)
        def disambiguator(*args: Any, **kwargs: Any) -> int:
            if not kwargs and len(args) == 1:
                arg = args[0]
            elif not args and len(kwargs) == 1:
                arg = next(iter(kwargs.values()))
            else:
                return func(*args, **kwargs) or 0  # type: ignore

            if not isinstance(arg, list):
                raise TypeError(f"arg '{arg}' of '{func}' must be a list of strings.")
            return wrapper(arg)  # type: ignore

        return disambiguator

    if maybe_func is None:
        return decorator
    return decorator(maybe_func)
