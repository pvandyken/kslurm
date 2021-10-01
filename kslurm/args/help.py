from __future__ import absolute_import

import textwrap
from pathlib import Path
from typing import Any, Iterable, List, Optional, TypeVar, Union, cast

from rich.console import Group
from rich.padding import Padding
from rich.table import Table  # type: ignore (Claims Table is not exported??)
from rich.text import Text

from kslurm.style.console import console

from .arg_types import (
    Arg,
    ChoiceArg,
    FlagArg,
    KeywordArg,
    PositionalArg,
    ShapeArg,
    TailArg,
)
from .helpers import get_arg_list, group_by_type


def _syntax_format(syntax: str):
    lines = [f"[cyan bold]{line.strip()}[/]" for line in syntax.split(" | ")]
    return "\n".join(lines)


def _header(header: str):
    return f"[bold green]{header.upper()}[/bold green]"


def _section(header: str, body: Union[Table, str]):
    return (
        Group(Padding.indent(_header(header), 4), Padding.indent(body, 8), "\n")
        if body
        else ""
    )


def print_help(script: str, models: object, script_help: str = "") -> None:
    arg_list = get_arg_list(models)
    grouped = group_by_type(arg_list)
    positionals = cast(List[PositionalArg[Any]], grouped.get(PositionalArg, []))
    shapes = cast(List[ShapeArg[Any]], grouped.get(ShapeArg, []))
    keywords = cast(List[KeywordArg[Any]], grouped.get(KeywordArg, []))
    flags = cast(List[FlagArg], grouped.get(FlagArg, []))
    choices = cast(List[ChoiceArg[Any]], grouped.get(ChoiceArg, []))
    tail = cast(List[TailArg], grouped.get(TailArg, []))
    positional_names = [arg.name for arg in positionals]
    script_name = Path(script).name

    command_line_example = (
        f"[b]USAGE:[/] {script_name} [hot]<keywords and flags>[/] "
        f"{' '.join(positional_names)}"
    )
    if tail:
        command_line_example += f" [cyan]<{tail[0].name.lower()}>[/]"
    command_line_example += "\n\n"

    shape_section = _section("Shape args", _shape_table(shapes))
    keyword_section = _section("keyword args", _keyword_table(keywords))
    positional_section = _section("positional args", _positional_table(positionals))
    flag_section = _section("flag args", _flag_table(flags))
    choice_section = _section("choice args", _choice_table(choices))
    sections = list(
        filter(
            None,
            [
                "\n",
                command_line_example,
                script_help,
                choice_section,
                positional_section,
                shape_section,
                keyword_section,
                flag_section,
            ],
        )
    )
    console.print(*sections)


T = TypeVar("T", bound=Arg[Any])


def _get_helps(args: List[T]):
    return [Text(textwrap.fill(arg.help, 70)) for arg in args]


def _get_defaults(args: List[Any]):
    return [Text(str(arg), style="default_col") for arg in args]


def _help_table(
    rows: Iterable[Iterable[Union[Text, str]]],
    header: Optional[List[str]] = None,
    right_aligned_cols: int = 1,
):
    t = Table.grid(
        padding=(1, 2),
    )
    for _ in range(right_aligned_cols):
        t.add_column(justify="right")
    if header:
        t.add_row(*header, style="bold")
    for r in rows:
        t.add_row(*list(r))
    return t


def _shape_table(args: List[ShapeArg[Any]]):
    if args:
        names = [Text(arg.name, style="bold") for arg in args]
        syntaxes = [_syntax_format(arg.syntax) for arg in args]
        examples = [Text("\n".join(arg.examples), style="grey") for arg in args]
        eg = ["➔" if example else "" for example in examples]
        defaults = _get_defaults([arg.raw_value for arg in args])
        helps = _get_helps(args)

        header = ["", "Syntax", "", "Examples", "Default", ""]
        body = zip(names, syntaxes, eg, examples, defaults, helps)

        return _help_table(body, header, right_aligned_cols=2)
    else:
        return ""


def _positional_table(args: List[PositionalArg[Any]]):
    if args:
        names = [Text(arg.name, style="bold") for arg in args]
        defaults = _get_defaults([arg.raw_value for arg in args])
        helps = _get_helps(args)
        body = zip(names, defaults, helps)
        header = ["", "Default", ""]
        return _help_table(body, header)
    else:
        return ""


def _keyword_table(args: List[KeywordArg[Any]]):
    if args:
        names = [Text(", ".join(arg.match_list), style="bold") for arg in args]
        value_names = [f"<[i]{arg.values_name}[/]>" for arg in args]
        defaults = _get_defaults([arg.values for arg in args])
        helps = _get_helps(args)

        body = zip(names, value_names, defaults, helps)
        header = ["", "", "Default", ""]
        return _help_table(body, header)
    else:
        return ""


def _flag_table(args: List[FlagArg]):
    if args:
        names = [Text(", ".join(arg.match_list), style="bold") for arg in args]
        helps = _get_helps(args)

        body = zip(names, helps)
        return _help_table(body)
    else:
        return ""


def _choice_table(args: List[ChoiceArg[Any]]):
    if args:
        names = [Text(arg.name, style="bold") for arg in args]
        choices = [Text(", ".join(arg.match_list), style="bold") for arg in args]
        helps = _get_helps(args)
        defaults = _get_defaults([arg.raw_value for arg in args])

        body = zip(names, choices, defaults, helps)
        return _help_table(body)
    else:
        return ""
