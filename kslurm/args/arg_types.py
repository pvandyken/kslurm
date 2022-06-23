from __future__ import absolute_import, annotations

import uuid
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, TypeVar

import attr

import kslurm.args.actions as actions
import kslurm.args.matchers as matchers
from kslurm.args.arg import Arg, ParamSet, Parser
from kslurm.args.help_templates import PositionalArg, ShapeArg, SubcommandTemplate
from kslurm.args.protocols import WrappedCommand
from kslurm.exceptions import ValidationError

T = TypeVar("T")
S = TypeVar("S")

Subcommand = tuple[str, WrappedCommand]


def positional(
    default: Optional[T] = None,
    *,
    help: str = "",
    name: str = "",
    format: Callable[[str], T] = actions.NO_CONVERT,
) -> Arg[T]:
    return Arg[T](
        parser=Parser(
            priority=0,
            match=matchers.everything(),
            action=actions.convert(format).replace(),
        ),
        help=help,
        help_template=PositionalArg(),
        name=name,
        default=default,
    )


def choice(
    match: List[str],
    *,
    default: Optional[T] = None,
    help: str = "",
    name: str = "",
    format: Callable[[str], T] = actions.NO_CONVERT,
) -> Arg[T]:
    def check_match(val: str) -> T:
        if val in match:
            return format(val)
        choices = "\n".join([f"\t• {m}" for m in match])
        raise ValidationError(f"Please select between:\n{choices}")

    choices = ", ".join(match)
    return Arg[T](
        parser=Parser(
            match=matchers.everything(),
            priority=0,
            action=actions.convert(check_match).replace(),
        ),
        help=f"{help} - options: [{choices}]",
        help_template=PositionalArg(),
        name=name,
        default=default,
    )


def subcommand(
    commands: Dict[str, WrappedCommand],
    default: Optional[str] = None,
):
    def check_match(val: str):
        if val in commands.keys():
            return (val, commands[val])
        choices = "\n".join([f"\t\t• {m}" for m in commands.keys()])
        raise ValidationError(f"Please select between:\n{choices}")

    return Arg(
        parser=Parser(
            match=matchers.everything(),
            priority=0,
            action=actions.convert(check_match).replace(),
            terminal=True,
        ),
        help="Run any command followed by -h for more information",
        help_template=SubcommandTemplate(commands),
        name="subcommand",
        default=check_match(default) if default else None,
    )


def shape(
    match: str,
    *,
    default: Optional[T] = None,
    format: Callable[[str], T] = actions.NO_CONVERT,
    help: str = "",
    name: str = "",
    syntax: str = "",
    examples: List[str] = [],
) -> Arg[T]:
    return Arg[T](
        parser=Parser(
            match=matchers.regex(match),
            priority=10,
            action=actions.convert(format).replace(),
        ),
        help=help,
        help_template=ShapeArg(
            syntax=syntax,
            examples=examples,
        ),
        name=name,
        default=default,
    )


def path(
    *,
    default: Optional[Path] = None,
    dir_only: bool = False,
    help: str = "",
    name: str = "",
) -> Arg[Path]:
    return Arg[Path](
        parser=Parser(
            match=matchers.path(is_dir=dir_only),
            priority=10,
            action=actions.convert(Path).replace(),
        ),
        help=help,
        name=name,
        default=default,
    )


def flag(
    match: list[str],
    default: Optional[bool] = False,
    help: str = "",
) -> Arg[bool]:

    return Arg[bool](
        parser=Parser(
            match=matchers.choice(*match).settings(duplicates=True),
            priority=20,
            action=actions.convert(bool).replace(),
        ),
        help=help,
        name=", ".join(match),
        default=default,
    )


def keyword(
    match: list[str],
    *,
    default: Optional[Any] = attr.NOTHING,
    format: Callable[[str], Any] = actions.NO_CONVERT,
    num: Optional[int] = None,
    help: str = "",
    lazy: bool = False,
    id: str = "",
) -> Any:
    pid = str(uuid.uuid4().int)
    action = (
        actions.convert(format).replace()
        if num is None
        else actions.convert(format).append()
    )
    return ParamSet(
        parent=Parser(
            id=pid,
            match=matchers.choice(*match).settings(duplicates=True),
            priority=20,
            action=actions.convert(bool).replace(),
        ),
        child=Parser(
            match=matchers.option_chain(pid, num or 1, matchers.everything()),
            priority=5 if lazy else 30,
            action=action,
        ),
        help=help,
        name=", ".join(match) + " <value>",
        default=default,
        id=id,
    )


class HelpRequest(Exception):
    pass


def help_parser() -> Parser[bool]:
    return Parser(
        match=matchers.choice("--help", "-h").settings(duplicates=True),
        priority=20,
        action=actions.raises(HelpRequest()),
        value=False,
    )
