from __future__ import absolute_import

from typing import Any, Callable, Dict, Optional, TypeVar, overload

import kslurm.args.arg_types as arg_types
from kslurm.args.types import WrappedCommand

T = TypeVar("T")

Subcommand = arg_types.Subcommand


@overload
def positional(
    default: Optional[str] = ...,
    *,
    help: str = ...,
    name: str = ...,
) -> Any:
    ...


@overload
def positional(
    default: Optional[str] = ...,
    *,
    format: Callable[[str], T] = ...,
    help: str = ...,
    name: str = ...,
) -> T:
    ...


def positional(*args: Any, **kwargs: Any):  # type: ignore
    return arg_types.positional(*args, **kwargs)


@overload
def choice(
    match: list[str],
    *,
    default: Optional[str] = None,
    help: str = "",
    name: str = "",
) -> Any:
    ...


@overload
def choice(
    match: list[str],
    *,
    default: Optional[str] = ...,
    format: Callable[[str], T] = ...,
    help: str = ...,
    name: str = ...,
) -> T:
    ...


def choice(*args: Any, **kwargs: Any):  # type: ignore
    return arg_types.choice(*args, **kwargs)


def subcommand(
    commands: Dict[str, WrappedCommand],
    default: Optional[str] = None,
) -> arg_types.Subcommand:
    return arg_types.subcommand(commands, default)  # type: ignore


@overload
def shape(
    match: Callable[[str], bool],
    *,
    default: Optional[str] = None,
    help: str = "",
    name: str = "",
    syntax: str = "",
    examples: list[str] = [],
) -> Any:
    ...


@overload
def shape(
    match: Callable[[str], bool],
    *,
    default: Optional[str] = None,
    format: Callable[[str], T] = str,
    help: str = "",
    name: str = "",
    syntax: str = "",
    examples: list[str] = [],
) -> T:
    ...


def shape(  # type: ignore
    *args: Any,
    **kwargs: Any,
):
    return arg_types.shape(*args, **kwargs)


def flag(
    match: list[str],
    default: Optional[bool] = False,
    help: str = "",
) -> bool:
    return arg_types.flag(match, default, help)  # type: ignore


@overload
def keyword(
    match: list[str],
    *,
    default: list[str] = ...,
    num: int = ...,
    lazy: bool = ...,
    help: str = ...,
) -> Any:
    ...


@overload
def keyword(
    match: list[str],
    *,
    default: list[str] = ...,
    num: int = ...,
    validate: Callable[[str], T] = ...,
    lazy: bool = ...,
    help: str = ...,
) -> list[T]:
    ...


def keyword(  # type: ignore
    *args: Any,
    **kwargs: Any,
):
    return arg_types.keyword(*args, **kwargs)
