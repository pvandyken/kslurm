from __future__ import absolute_import, annotations

import functools as ft
import inspect
import itertools as it
import sys
from typing import Any, Callable, Literal, Optional, TypeVar, Union, overload

import attr
import docstring_parser as doc
from rich.text import Text
from typing_extensions import ParamSpec

from kslurm.args.arg import Arg, Parser
from kslurm.args.arg_types import HelpRequest, help_parser
from kslurm.args.help import HelpText
from kslurm.args.helpers import get_arg_dict, get_parsers, read_parsers
from kslurm.args.parser import parse_args
from kslurm.args.protocols import Command
from kslurm.exceptions import CommandLineError, TailError
from kslurm.style import console, stderr

P = ParamSpec("P")
_CommandFunc = Callable[P, Optional[int]]
ModelType = Union[dict[str, Arg[Any]], type]


Parsers = dict[str, Parser[Any]]


def error(argv: list[str] = []):
    return 1


class CommandArgs:
    _model: Optional[str] = None
    _tail: Optional[str] = None
    _modellist: Optional[str] = None
    _name: Optional[str] = None
    _helptext: Optional[str] = None

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

    @property
    def helptext(self):
        return self._helptext

    @helptext.setter
    def helptext(self, value: str):
        if self._helptext is not None:
            raise ValueError("helptext is already set")
        self._helptext = value


Exc = TypeVar("Exc", bound=type[Exception], covariant=True)


class CommandError(Exception):
    def __init__(self, msg: str, *args: Any):
        super().__init__(msg, *args)
        self.msg = msg


@overload
def command(
    maybe_func: None = ...,
    *,
    terminate_on_unknown: bool = ...,
    inline: bool = ...,
    allow_unknown: bool = False,
) -> Callable[[_CommandFunc[P]], Command[P]]:
    ...


@overload
def command(
    maybe_func: _CommandFunc[P],
    *,
    terminate_on_unknown: Literal[True] = ...,
    inline: Literal[False] = ...,
    allow_unknown: bool = False,
) -> Command[P]:
    ...


def command(
    maybe_func: Optional[_CommandFunc[P]] = None,
    *,
    terminate_on_unknown: bool = False,
    inline: bool = False,
    allow_unknown: bool = False,
) -> Union[Command[P], Callable[[_CommandFunc[P]], Command[P]]]:
    @attr.frozen
    class BlankModel:
        pass

    def decorator(func: _CommandFunc[P]):
        unknown = allow_unknown
        if not callable(func):
            raise CommandLineError(f"{func} is not callable")

        params = inspect.signature(func)
        exceptions: tuple[type[Exception], ...] = tuple()  # type: ignore
        model = BlankModel

        command_args = CommandArgs()
        if inline:
            model = attr.make_class(
                f"{func.__name__}__Model__",
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
            model.__doc__ = func.__doc__
        else:
            for param in params.parameters.values():
                annotation = (
                    eval(param.annotation, func.__globals__)
                    if isinstance(param.annotation, str)
                    else param.annotation
                )
                if annotation == param.empty:
                    raise CommandLineError(
                        f"parameter '{param}' in {func} must be annotated"
                    )
                if annotation == list[str]:
                    command_args.tail = param.name
                    unknown = True
                    continue
                if annotation == Parsers:
                    command_args.modellist = param.name
                    continue
                if annotation == str:
                    command_args.name = param.name
                    continue
                if annotation == HelpText:
                    command_args.helptext = param.name
                    continue

                if model is not BlankModel:
                    raise CommandLineError(
                        f"Mutliple models detected: {model} and {annotation}"
                    )
                model = annotation

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

        docobj = doc.parse(func.__doc__ or "")
        docstr = (
            (docobj.short_description or "")
            + (docobj.blank_after_short_description and "\n\n" or "\n")
            + (docobj.long_description or "")
        )

        model_dict = get_arg_dict(model)
        if command_args.tail:
            usage_suffix = "command_args"
        else:
            usage_suffix = ""

        class Wrapper:
            def get_helptext(self, entrypoint: str):
                return HelpText(entrypoint, model_dict, docstr, usage_suffix)

            @ft.wraps(func)
            def __call__(self, *args: P.args, **kwargs: P.kwargs):
                if inline:
                    for param in it.islice(
                        params.parameters.values(), len(args), len(params.parameters)
                    ):
                        if (
                            isinstance(param.default, Arg)
                            and param.default.assigned_value is None  # type: ignore
                        ):
                            raise SyntaxError(
                                f"Mandatory param '{param}' in function '{func}' not "
                                "provided a value"
                            )
                return func(*args, **kwargs) or 0

            @ft.wraps(func)
            def cli(self, argv: list[str] = sys.argv):
                helptext = self.get_helptext(argv[0])
                try:
                    parsed_list, tail = parse_args(
                        argv[1:],
                        {
                            **get_parsers(model_dict),
                            "help": help_parser().with_id("help"),
                        },
                        terminate_on_unknown=terminate_on_unknown,
                        allow_unknown=unknown,
                    )

                    parsed, errors = read_parsers(model_dict, parsed_list, False, False)

                    if errors or isinstance(tail, TailError):
                        console.print(helptext.with_usage_only())
                        for error in errors.values():
                            stderr.print(Text.from_ansi(error.msg))
                        if isinstance(tail, TailError):
                            print(tail.msg, file=sys.stderr)
                        return 1
                    if not inline:
                        args: dict[str, Any] = {}

                        if command_args.model is not None:
                            args[command_args.model] = model(**parsed)

                        if command_args.tail is not None:
                            args[command_args.tail] = tail

                        if command_args.modellist is not None:
                            args[command_args.modellist] = parsed_list

                        if command_args.name is not None:
                            args[command_args.name] = argv[0]

                        if command_args.helptext is not None:
                            args[command_args.helptext] = helptext
                    else:
                        args = parsed

                except (HelpRequest, *exceptions) as err:
                    if isinstance(err, HelpRequest) and not isinstance(err, exceptions):
                        console.print(helptext)
                        return 0

                    args: dict[str, Any] = {}
                    if command_args.model is not None:
                        args[command_args.model] = err

                    if command_args.tail is not None:
                        args[command_args.tail] = argv[1:]

                    if command_args.modellist is not None:
                        args[command_args.modellist] = {}

                    if command_args.name is not None:
                        args[command_args.name] = argv[0]

                    if command_args.helptext is not None:
                        args[command_args.helptext] = helptext
                try:
                    return func(**args) or 0  # type: ignore
                except CommandError as err:
                    print(err.msg, file=sys.stderr)
                    return 1

        return Wrapper()

    if maybe_func is None:
        return decorator
    return decorator(maybe_func)
