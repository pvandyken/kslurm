from __future__ import absolute_import

import itertools as it
import operator as op
from pathlib import Path
from typing import Any, DefaultDict, Optional, Union

from rich.console import Group
from rich.padding import Padding
from rich.table import Table
from rich.text import Text

from kslurm.args.arg import AbstractHelpTemplate, Arg
from kslurm.style.console import console


class BasicTemplate(AbstractHelpTemplate):
    title = "options"
    header = []
    cls_usage = "<options>"
    priority = 50

    def row(self, name: str, help: str, default: Optional[str]):
        return [name, help, default if default is not None else ""]


def _header(header: str):
    return f"[bold green]{header.upper()}[/bold green]"


def _section(header: str, body: Union[Table, str]):
    return (
        Group(Padding.indent(_header(header), 4), Padding.indent(body, 8), "\n")
        if body
        else ""
    )


def print_help(
    script: str,
    models: list[Arg[Any, Any]],
    script_help: str = "",
    usage_suffix: str = "",
) -> None:
    script_name = Path(script).name

    templates: set[type[AbstractHelpTemplate]] = set()
    usages: dict[type[AbstractHelpTemplate], list[str]] = DefaultDict(list)
    for model in models:
        if model.help_template is None:
            template = BasicTemplate()
        else:
            template = model.help_template
        args = model.label, model.help, str(model.safe_value or "")
        template.add_row(*args)
        try:
            usages[type(template)].append(template.usage(*args))
        except NotImplementedError:
            pass
        templates.add(type(template))

    sorted_templates: dict[type[AbstractHelpTemplate], list[str]] = {}

    for template in sorted(usages, key=op.attrgetter("priority"), reverse=True):
        if not usages[template]:
            usages[template].append(template.cls_usage)
        sorted_templates[template] = usages[template]

    command_line_example = [
        "[b]USAGE:[/] ",
        script_name,
        " " + " ".join(it.chain.from_iterable(sorted_templates.values()))
        if usages
        else "",
        Text(f" <{usage_suffix}>", style="cyan") if usage_suffix else "",
        "\n",
    ]

    sections = [_section(template.title, template.table()) for template in templates]

    console.print(*command_line_example, script_help, *sections, sep="")
