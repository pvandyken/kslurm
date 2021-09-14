from typing import Any, List, TypeVar, cast
import textwrap
import itertools as it
from tabulate import tabulate
from .arg_types import Arg, FlagArg, KeywordArg, PositionalArg, ShapeArg
from .helpers import group_by_type, get_arg_list
from cluster_utils.colors import bold, dim, green, cyan, magenta

def syntax_format(syntax: str):
    lines = [cyan(bold(line.strip())) for line in syntax.split(" | ")]
    return "\n".join(lines)

def header(header: str): 
    return bold(green(header.upper()))



def print_help(script_name: str, models: object) -> None:
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
    positional_names = [arg.name for arg in positionals]

    
    command_line_example = f"{bold('USAGE:')} {script_name} {magenta('<keywords and flags>')} {' '.join(positional_names)}"
    shape_section = "\n".join([
        indent(1, header('Shape args')),
        indent(2, shape_table(shapes))
    ]) if shapes else ""
    keyword_section = "\n".join([
        indent(1, header('keyword args')),
        indent(2, keyword_table(keywords))
    ]) if keywords else ""
    positional_section = "\n".join([
        indent(1, header('positional args')),
        indent(2, positional_table(positionals))
    ]) if positionals else ""
    flag_section = "\n".join([
        indent(1, header('flag args')),
        indent(2, flag_table(flags))
    ]) if flags else ""

    print("")
    print("\n\n".join(
        filter(None, [
            command_line_example,
            positional_section,
            shape_section,
            keyword_section,
            flag_section
    ])))
    print("")
    
    

T = TypeVar("T", bound=Arg[Any])

def get_helps(args: List[T]):
    return [textwrap.fill(arg.help, 70) for arg in args]

def indent(indents: int, text: str):
    tabchars = "".join(it.repeat("\t", indents))
    textl = [tabchars + line for line in text.splitlines()]
    return "\n".join(textl)


def shape_table(args: List[ShapeArg[Any]]):
    names = [bold(arg.name) for arg in args]
    syntaxes = [syntax_format(arg.syntax) for arg in args]
    examples = ["\n".join(map(dim, arg.examples)) for arg in args]
    eg = ["➔" if example else "" for example in examples ]
    helps = get_helps(args)

    return tabulate(
        zip(names, syntaxes, eg, examples, helps),
        #list(map(bold, ["Name", "Syntax", "Examples", "Help"])),
        colalign=("right", "right"),
        tablefmt="plain")

def positional_table(args: List[PositionalArg[Any]]):
    names = [bold(arg.name) for arg in args]
    helps = get_helps(args)
    return tabulate(
        zip(names, helps),
        colalign=("right",),
        tablefmt="plain"
    )

def keyword_table(args: List[KeywordArg[Any]]):
    names = [bold(', '.join(arg.match_list)) for arg in args]
    value_names = [dim(f"[{arg.values_name}]") for arg in args]
    helps = get_helps(args)
    return tabulate(
        zip(names, value_names, helps),
        colalign=("right",),
        tablefmt="plain"
    )

def flag_table(args: List[FlagArg]):
    names = [bold(', '.join(arg.match_list)) for arg in args]
    helps = get_helps(args)
    return tabulate(
        zip(names, helps),
        colalign=('right',),
        tablefmt=("plain")
    )



