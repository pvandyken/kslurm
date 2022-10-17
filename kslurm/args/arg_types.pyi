from __future__ import absolute_import

from pathlib import Path
from typing import Any, Callable, Literal, NoReturn, Optional, TypeVar, overload

from typing_extensions import ParamSpec

import kslurm.args.arg_types as arg_types
from kslurm.args.arg import ParamSet, Parser
from kslurm.args.command import Command
from kslurm.args.protocols import WrappedCommand
from kslurm.exceptions import ValidationError

T = TypeVar("T")
P = ParamSpec("P")

Subcommand = tuple[str, WrappedCommand]

@overload
def positional(
    default: Literal[None] = ...,
    *,
    help: str = ...,
    name: str = ...,
) -> Any: ...
@overload
def positional(
    default: Literal[None] = ...,
    *,
    format: Callable[[str], T],
    help: str = ...,
    name: str = ...,
) -> T: ...
@overload
def positional(
    default: T,
    *,
    format: Callable[[str], T] = ...,
    help: str = ...,
    name: str = ...,
) -> T: ...
@overload
def choice(
    match: list[str],
    *,
    default: Literal[None] = ...,
    help: str = ...,
    name: str = ...,
) -> Any: ...
@overload
def choice(
    match: list[str],
    *,
    default: Literal[None] = ...,
    format: Callable[[str], T],
    help: str = ...,
    name: str = ...,
) -> T: ...
@overload
def choice(
    match: list[str],
    *,
    default: T,
    format: Callable[[str], T] = ...,
    help: str = ...,
    name: str = ...,
) -> T: ...
def subcommand(
    commands: dict[str, WrappedCommand | Command[...] | Command[[]]],
    default: Optional[WrappedCommand | Command[...] | Command[[]]] = ...,
) -> arg_types.Subcommand: ...

class InvalidSubcommand(ValidationError):
    pass

@overload
def shape(
    match: str,
    *,
    default: None = ...,
    help: str = ...,
    name: str = ...,
    syntax: str = ...,
    examples: list[str] = ...,
) -> Any: ...
@overload
def shape(
    match: str,
    *,
    default: None = ...,
    help: str = ...,
    format: Callable[[str], T],
    name: str = ...,
    syntax: str = ...,
    examples: list[str] = ...,
) -> T: ...
@overload
def shape(
    match: str,
    *,
    default: T,
    help: str = ...,
    format: Callable[[str], T] = ...,
    name: str = ...,
    syntax: str = ...,
    examples: list[str] = ...,
) -> T: ...
def path(
    *,
    default: Optional[Path] = ...,
    dir_only: bool = ...,
    help: str = ...,
    name: str = ...,
) -> Path: ...
def flag(
    match: list[str],
    default: Optional[bool] = ...,
    help: str = ...,
) -> bool: ...
@overload
def keyword(
    match: list[str],
    *,
    default: None = ...,
    num: None = ...,
    lazy: bool = ...,
    help: str = ...,
) -> Any: ...
@overload
def keyword(
    match: list[str],
    *,
    default: None = ...,
    num: int,
    lazy: bool = ...,
    help: str = ...,
) -> list[Any]: ...
@overload
def keyword(
    match: list[str],
    *,
    default: T,
    format: Callable[[str], T] = ...,
    num: None = ...,
    lazy: bool = ...,
    help: str = ...,
) -> T: ...
@overload
def keyword(
    match: list[str],
    *,
    default: Optional[Any] = ...,
    format: Callable[[str], Any] = ...,
    num: Literal[0],
    lazy: bool = ...,
    help: str = ...,
) -> NoReturn: ...
@overload
def keyword(
    match: list[str],
    *,
    default: list[T],
    format: Callable[[str], T] = ...,
    num: int,
    lazy: bool = ...,
    help: str = ...,
) -> list[T]: ...
@overload
def keyword(
    match: list[str],
    *,
    default: Optional[T] = ...,
    format: Callable[[str], T],
    num: None = ...,
    lazy: bool = ...,
    help: str = ...,
) -> T: ...
@overload
def keyword(
    match: list[str],
    *,
    default: Optional[list[T]] = ...,
    format: Callable[[str], T],
    num: int,
    lazy: bool = ...,
    help: str = ...,
) -> list[T]: ...
@overload
def keyword(
    match: list[str],
    *,
    default: Any = ...,
    format: Callable[[str], Any] = ...,
    num: int = ...,
    lazy: bool = ...,
    help: str = ...,
    id: str,
) -> ParamSet[Any]: ...

class HelpRequest(Exception): ...

def help_parser() -> Parser[bool]: ...
