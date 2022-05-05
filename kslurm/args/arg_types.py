from __future__ import absolute_import, annotations

from typing import Callable, Dict, List, Optional, TypeVar, Union

import attr
import docstring_parser as doc
from rich.text import Text

from kslurm.args.arg import AbstractHelpTemplate, Arg, DuplicatePolicy, HelpRow
from kslurm.args.types import WrappedCommand
from kslurm.exceptions import ValidationError

T = TypeVar("T")
S = TypeVar("S")


@attr.frozen
class ShapeArg(AbstractHelpTemplate):
    title = "Shape Args"
    header = ["", "Syntax", "", "Examples", "Default", ""]
    right_align_cols = 2

    syntax: str
    examples: list[str]

    def _syntax_format(self, syntax: str):
        lines = [f"[cyan bold]{line.strip()}[/]" for line in syntax.split(" | ")]
        return "\n".join(lines)

    def usage(self, name: str, help: str, default: Optional[str]) -> str:
        return rf"[hot]\[{name}][/]"

    def row(self, name: str, help: str, default: Optional[str]):
        return [
            Text(name, style="bold"),
            self._syntax_format(self.syntax),
            ("➔" if self.examples else ""),
            Text("\n".join(self.examples)),
            Text(str(default), style="default_col") if default is not None else "",
            Text(help),
        ]


@attr.frozen
class PositionalArg(AbstractHelpTemplate):
    title = "Positional Args"
    header = []

    def usage(self, name: str, help: str, default: Optional[str]) -> str:
        if default is None:
            return f"[cyan]{name}[/]"
        return rf"[cyan]\[{name}][/]"

    def row(self, name: str, help: str, default: Optional[str]):
        return [
            Text(name, style="bold"),
            Text(default if default is not None else "REQUIRED", style="default_col"),
            Text(help),
        ]


@attr.frozen
class SubcommandTemplate(AbstractHelpTemplate):
    title = "Commands"
    header = []

    commands: dict[str, WrappedCommand]

    def usage(self, name: str, help: str, default: Optional[str]) -> str:
        return f"[cyan]{name}[/]"

    def row(
        self, name: str, help: str, default: Optional[str]
    ) -> Union[list[HelpRow], HelpRow]:
        return [
            ["", help],
            [],
            *(
                [
                    Text(name, style="bold"),
                    Text(doc.parse(func.__doc__ or "").short_description or ""),
                ]
                for name, func in self.commands.items()
            ),
        ]


# @attr.frozen
# class KeywordArg(AbstractHelpEntry):
#     title = "Keyword Args"
#     header = ["", "Default", ""]

#     name: list[str]
#     value_name: Optional[str]
#     default: str
#     help: str

#     @property
#     def usage(self):
#         return ""

#     def row(self) -> list[Union[Text, str]]:
#         return [
#             Text(", ".join(self.name)) + (
#                 Text(f" <{(self.value_name)}>", style="grey")
#                 if self.value_name else ''
#             ),
#             Text(self.default, style="default_col"),
#             Text(textwrap.fill(self.help, 70)),
#         ]


# @attr.frozen
# class ChoiceArg(AbstractHelpEntry):
#     title = "Choice Args"
#     header = ["", "Choices", "Default", ""]

#     name: str
#     choices: list[str]
#     default: str
#     help: str

#     @property
#     def usage(self):
#         return ""

#     def row(self) -> list[Union[Text, str]]:
#         return [
#             Text(self.name, style="bold"),
#             Text(",".join(self.choices), style="bold"),
#             Text(self.default, style="default_col"),
#             Text(textwrap.fill(self.help, 70)),
#         ]


def positional(
    default: Optional[str] = None,
    *,
    help: str = "",
    name: str = "",
    format: Callable[[str], T] = str,
) -> Arg[T, None]:
    return Arg[T, None](
        priority=0,
        match=lambda _: True,
        duplicates=DuplicatePolicy.SKIP,
        format=format,
        help=help,
        help_template=PositionalArg(),
        name=name,
    ).with_value(default)


def choice(
    match: List[str],
    *,
    default: Optional[str] = None,
    help: str = "",
    name: str = "",
    format: Callable[[str], T] = str,
) -> Arg[T, None]:
    def check_match(val: str) -> T:
        if val in match:
            return format(val)
        choices = "\n".join([f"\t\t• {m}" for m in match])
        raise ValidationError(f"Please select between:\n" f"{choices}")

    return Arg[T, None](
        match=lambda _: True,
        priority=0,
        duplicates=DuplicatePolicy.SKIP,
        format=check_match,
        help=help,
        name=name,
    ).with_value(default)


Subcommand = tuple[str, WrappedCommand]


def subcommand(
    commands: Dict[str, WrappedCommand],
    default: Optional[str] = None,
) -> Arg[Subcommand, None]:
    def check_match(val: str):
        if val in commands.keys():
            return (val, commands[val])
        choices = "\n".join([f"\t\t• {m}" for m in commands.keys()])
        raise ValidationError(f"Please select between:\n" f"{choices}")

    return Arg[Subcommand, None](
        match=lambda _: True,
        priority=0,
        duplicates=DuplicatePolicy.SKIP,
        format=check_match,
        help="Run any command followed by -h for more information",
        help_template=SubcommandTemplate(commands),
        name="subcommand",
        terminal=True,
    ).with_value(default)


def shape(
    match: Callable[[str], bool],
    *,
    default: Optional[str] = None,
    format: Callable[[str], T] = str,
    help: str = "",
    name: str = "",
    syntax: str = "",
    examples: List[str] = [],
) -> Arg[T, None]:
    return Arg[T, None](
        match=match,
        priority=10,
        duplicates=DuplicatePolicy.SKIP,
        format=format,
        help=help,
        help_template=ShapeArg(
            syntax=syntax,
            examples=examples,
        ),
        name=name,
    ).with_value(default)


def flag(
    match: List[str],
    default: Optional[bool] = False,
    help: str = "",
) -> Arg[bool, None]:
    def check_match(val: str):
        if val in match:
            return True
        return False

    if default:
        raw_value = match[0]
    elif default is None:
        raw_value = None
    else:
        raw_value = ""

    return Arg[bool, None](
        match=check_match,
        priority=20,
        duplicates=DuplicatePolicy.REPLACE,
        format=bool,
        help=help,
        name=", ".join(match),
    ).with_value(raw_value)


def keyword(
    match: List[str],
    *,
    default: Optional[List[str]] = [],
    validate: Callable[[str], T] = str,
    num: int = 1,
    help: str = "",
    lazy: bool = ...,
) -> Arg[bool, T]:
    def check_match(val: str):
        if val in match:
            return True
        return False

    if default:
        raw_value = match[0]
    elif default is None:
        raw_value = None
    else:
        raw_value = ""

    return (
        Arg[bool, T](
            match=check_match,
            priority=20,
            duplicates=DuplicatePolicy.REPLACE,
            format=bool,
            help=help,
            num=num,
            validate=validate,
            greediness=5 if lazy else 30,
            name=", ".join(match) + " <value>",
        )
        .with_value(raw_value)
        .with_values(default or [])
    )
