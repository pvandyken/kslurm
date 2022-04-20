from __future__ import absolute_import

import inspect
import sys
from typing import Any, Callable, List

from typing_extensions import Protocol

from kslurm import parse_args
from kslurm.exceptions import CommandLineError


class WrappedCommand(Protocol):
    def __call__(self, argv: List[str] = ...) -> None:
        ...


def command(func: Callable[[Any], None]) -> WrappedCommand:
    if not callable(func):
        raise CommandLineError(f"{func} is not callable")

    params = inspect.signature(func)
    if len(params.parameters) > 1 or not len(params.parameters):
        raise CommandLineError(
            f"{func} must have a single, named arg. Currently: "
            f"{inspect.signature(func)}"
        )
    param = next(iter(params.parameters.values()))
    if param.annotation == param.empty:
        raise CommandLineError(f"parameter '{param}' in {func} must be annotated")
    model = param.annotation
    if isinstance(model, str):
        model = eval(model, func.__globals__)

    exceptions: Any = tuple()
    types = getattr(model, "__args__", None)
    if types is not None:
        model = types[0]
        exceptions = types[1:]

    if not isinstance(model, type):
        raise CommandLineError(
            f"Annotation of {param} in {func} must refer to a class type (currently "
            f"{type(model)})"
        )

    def wrapper(argv: List[str] = sys.argv):
        doc = func.__doc__
        if doc is None:
            doc = ""

        try:
            parsed = parse_args(argv[1:], model(), script_name=argv[0], docstring=doc)
        except exceptions as err:
            parsed = err
        func(parsed)

    return wrapper
