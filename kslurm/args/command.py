from __future__ import absolute_import

import inspect
import sys
from typing import Any, Callable, List, Union

import attr

from kslurm.args.parser import parse_args
from kslurm.args.types import WrappedCommand
from kslurm.exceptions import CommandLineError

_CommandFunc = Union[Callable[[Any], None], Callable[[], None]]


def command(func: _CommandFunc) -> WrappedCommand:
    @attr.frozen
    class BlankModel:
        pass

    if not callable(func):
        raise CommandLineError(f"{func} is not callable")

    params = inspect.signature(func)
    exceptions: Any = tuple()
    model = BlankModel
    if len(params.parameters) > 1:
        raise CommandLineError(
            f"{func} must have a single, named arg. Currently: "
            f"{inspect.signature(func)}"
        )
    if len(params.parameters):
        param = next(iter(params.parameters.values()))
        if param.annotation == param.empty:
            raise CommandLineError(f"parameter '{param}' in {func} must be annotated")
        model = param.annotation
        if isinstance(model, str):
            model = eval(model, func.__globals__)

        types = getattr(model, "__args__", None)
        if types is not None:
            model = types[0]
            exceptions = types[1:]

        if not isinstance(model, type):
            raise CommandLineError(
                f"Annotation of {param} in {func} must refer to a class type "
                f"(currently {type(model)})"
            )

    def wrapper(argv: List[str] = sys.argv):
        doc = func.__doc__
        if doc is None:
            doc = ""

        try:
            parsed = parse_args(argv[1:], model(), script_name=argv[0], docstring=doc)
        except exceptions as err:
            parsed = err
        try:
            func(parsed)  # type: ignore
        except TypeError:
            func()  # type: ignore

    return wrapper
