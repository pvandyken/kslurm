from typing import Any, List, TypeVar, cast

import textwrap
import itertools as it
from pathlib import Path

from tabulate import tabulate

from .arg_types import Arg, FlagArg, KeywordArg, PositionalArg, ShapeArg, TailArg
from .helpers import group_by_type, get_arg_list
from kslurm.colors import bold, dim, green, cyan, magenta

def _syntax_format(syntax: str):
    lines = [cyan(bold(line.strip())) for line in syntax.split(" | ")]
    return "\n".join(lines)

def _header(header: str): 
    return bold(green(header.upper()))

def _section(header: str, body: str):
    return "\n".join([
        _indent(1, _header(header)),
        _indent(2, body)
    ]) if body else ""

def print_help(script: str, models: object, script_help: str = "") -> None:
    arg_list = get_arg_list(models)
    grouped = group_by_type(arg_list)
    positionals =  cast(
        List[PositionalArg[Any]], 
        grouped.get(PositionalArg, [])
    )
    shapes = cast(
        List[ShapeArg[Any]],
        grouped.get(ShapeArg, [])
    )
    keywords = cast(
        List[KeywordArg[Any]],
        grouped.get(KeywordArg, [])
    )
    flags = cast(
        List[FlagArg],
        grouped.get(FlagArg, [])
    )
    tail = cast(
        List[TailArg],
        grouped.get(TailArg, [])
    )
    positional_names = [arg.name for arg in positionals]
    script_name = Path(script).name

    
    command_line_example = f"{bold('USAGE:')} {script_name} {magenta('<keywords and flags>')} {' '.join(positional_names)}"
    if tail:
        command_line_example += " " + cyan(f"<{tail[0].name.lower()}>")
    shape_section = _section('Shape args', _shape_table(shapes))
    keyword_section = _section('keyword args', _keyword_table(keywords))
    positional_section = _section('positional args', _positional_table(positionals))
    flag_section = _section('flag args', _flag_table(flags))

    print("")
    print("\n\n".join(
        filter(None, [
            command_line_example,
            script_help,
            positional_section,
            shape_section,
            keyword_section,
            flag_section
    ])))
    print("")
    
    

T = TypeVar("T", bound=Arg[Any])

def _get_helps(args: List[T]):
    return [textwrap.fill(arg.help, 70) for arg in args]

def _indent(indents: int, text: str, tabwidth: int = 4):
    tabchar = "".join(it.repeat(" ", tabwidth))
    tabchars = "".join(it.repeat(tabchar, indents))
    textl = [tabchars + line for line in text.splitlines()]
    return "\n".join(textl)

def _get_defaults(args: List[Any]):
    return [magenta(str(arg)) for arg in args]

def _shape_table(args: List[ShapeArg[Any]]):
    if args:
        names = [bold(arg.name) for arg in args]
        syntaxes = [_syntax_format(arg.syntax) for arg in args]
        examples = ["\n".join(map(dim, arg.examples)) for arg in args]
        eg = ["➔" if example else "" for example in examples ]
        defaults = _get_defaults([arg.value for arg in args])
        helps = _get_helps(args)

        return tabulate(
            zip(names, syntaxes, eg, examples, defaults, helps),
            list(map(bold, ["\n", "Syntax", "", "Examples", "Default", ""])),
            colalign=("right", "right"),
            tablefmt="plain")
    else:
        return ""

def _positional_table(args: List[PositionalArg[Any]]):
    if args:
        names = [bold(arg.name) for arg in args]
        defaults = _get_defaults([arg.value for arg in args])
        helps = _get_helps(args)
        return tabulate(
            zip(names, defaults, helps),
            list(map(bold, ["\n", "Default", ""])),
            colalign=("right",),
            tablefmt="plain"
        )
    else:
        return ""

def _keyword_table(args: List[KeywordArg[Any]]):
    if args:
        names = [bold(', '.join(arg.match_list)) for arg in args]
        value_names = [dim(f"<{arg.values_name}>") for arg in args]
        defaults = _get_defaults([arg.values for arg in args])
        helps = _get_helps(args)
        return tabulate(
            zip(names, value_names, defaults, helps),
            list(map(bold, ["\n", "", "Default", ""])),
            colalign=("right",),
            tablefmt="plain"
        )
    else:
        return ""

def _flag_table(args: List[FlagArg]):
    if args:
        names = [bold(', '.join(arg.match_list)) for arg in args]
        helps = _get_helps(args)
        return tabulate(
            zip(names, helps),
            colalign=('right',),
            tablefmt=("plain")
        )
    else:
        return ""



