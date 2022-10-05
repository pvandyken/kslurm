from __future__ import absolute_import

import functools as ft
import inspect
import itertools as it
import sys
from typing import (
    Any,
    Callable,
    Generic,
    Literal,
    Optional,
    Protocol,
    TypeVar,
    Union,
    overload,
)

import attr
from typing_extensions import ParamSpec

from kslurm.args.arg import Arg, Parser
from kslurm.args.arg_types import HelpRequest, help_parser
from kslurm.args.help import print_help
from kslurm.args.helpers import get_arg_dict, get_parsers, read_parsers
from kslurm.args.parser import parse_args
from kslurm.exceptions import CommandLineError, TailError

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


Exc = TypeVar("Exc", bound=type[Exception], covariant=True)


class _Command(Protocol, Generic[P]):
    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> int:
        ...

    def cli(self, argv: list[str] = ...) -> int:
        ...


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
) -> Callable[[_CommandFunc[P]], _Command[P]]:
    ...


@overload
def command(
    maybe_func: _CommandFunc[P] = ...,  # type: ignore
    *,
    terminate_on_unknown: Literal[True] = ...,
    inline: Literal[False] = ...,
) -> _Command[P]:
    ...


def command(
    maybe_func: Optional[_CommandFunc[P]] = None,
    *,
    terminate_on_unknown: bool = False,
    inline: bool = False,
) -> Union[_Command[P], Callable[[_CommandFunc[P]], _Command[P]]]:
    @attr.frozen
    class BlankModel:
        pass

    def decorator(func: _CommandFunc[P]):
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
        else:
            for param in params.parameters.values():
                if param.annotation == param.empty:
                    raise CommandLineError(
                        f"parameter '{param}' in {func} must be annotated"
                    )
                if param.annotation == list[str]:
                    command_args.tail = param.name
                    continue
                if param.annotation == Parsers:
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

        class Wrapper:
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
                doc = func.__doc__ or ""

                model_dict = get_arg_dict(model)
                if command_args.tail:
                    usage_suffix = "command_args"
                else:
                    usage_suffix = ""
                try:
                    parsed_list, tail = parse_args(
                        argv[1:],
                        {
                            **get_parsers(model_dict),
                            "help": help_parser().with_id("help"),
                        },
                        terminate_on_unknown=terminate_on_unknown,
                    )

                    parsed, errors = read_parsers(model_dict, parsed_list, False, False)

                    if errors or isinstance(tail, TailError):
                        print_help(
                            argv[0], model_dict, doc, usage_suffix, just_usage=True
                        )
                        for error in errors.values():
                            print(error.msg, file=sys.stderr)
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
                    else:
                        args = parsed

                except (HelpRequest, *exceptions) as err:
                    if isinstance(err, HelpRequest) and not isinstance(err, exceptions):
                        print_help(argv[0], model_dict, doc, usage_suffix)
                        return 0

                    args: dict[str, Any] = {}
                    if command_args.model is not None:
                        args[command_args.model] = err

                    if command_args.tail is not None:
                        args[command_args.tail] = []

                    if command_args.modellist is not None:
                        args[command_args.modellist] = {}

                    if command_args.name is not None:
                        args[command_args.name] = argv[0]

                try:
                    return func(**args) or 0  # type: ignore
                except CommandError as err:
                    print(err.msg, file=sys.stderr)
                    return 1

        return Wrapper()

    if maybe_func is None:
        return decorator
    return decorator(maybe_func)
