from __future__ import absolute_import, annotations

import itertools as it
import operator as op
from pathlib import Path
from typing import Any, DefaultDict, Optional, Union

import attrs
from rich.console import Group
from rich.padding import Padding
from rich.table import Table
from rich.text import Text
from typing_extensions import Self

from kslurm.args.arg import SKIPHELP, AbstractHelpTemplate, Arg, ParamSet


class BasicTemplate(AbstractHelpTemplate):
    title = "options"
    header = []
    cls_usage = "<options>"
    priority = 50

    def row(self, name: str, help: str, default: Optional[str]):
        return (
            [name, help, default if default is not None else ""]
            if help is not SKIPHELP
            else None
        )

    def update_meta(self, **kwargs: Any) -> Self:
        raise NotImplementedError()

    @property
    def help(self):
        return ""


def _header(header: str):
    return f"[bold green]{header.upper()}[/bold green]"


def _section(header: str, description: str | None, body: Union[Table, str]):
    return Group(
        *filter(
            None,
            [
                Padding.indent(_header(header), 4),
                Padding.indent(description, 8) if description else None,
                Padding.indent(body, 8) if body else None,
                "\n",
            ],
        )
    )


@attrs.frozen
class HelpText:
    script: str
    models: dict[str, Union[Arg[Any], ParamSet[Any]]]
    script_help: str = ""
    usage_suffix: str = ""
    just_usage: bool = False

    def with_usage_only(self):
        return attrs.evolve(self, just_usage=True)

    def __str__(self):
        return str(self.__rich__())

    def __rich__(self):
        models = self.models
        script_name = Path(self.script).name

        templates: set[type[AbstractHelpTemplate]] = set()
        usages: dict[type[AbstractHelpTemplate], list[str]] = DefaultDict(list)
        for model in models.values():
            if model.help_template is None:
                template = BasicTemplate()
            else:
                template = model.help_template
            args = model.label, model.help, str(model.assigned_value or "")
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

        command_line_example = Text.assemble(
            ("USAGE: ", "b"),
            script_name,
            Text.from_markup(
                " " + " ".join(it.chain.from_iterable(sorted_templates.values()))
            )
            if usages
            else "",
            (f" <{self.usage_suffix}>", "cyan") if self.usage_suffix else "",
            "\n",
        )
        if self.just_usage:
            return Group(command_line_example)

        return Group(
            *filter(
                None,
                [
                    command_line_example,
                    self.script_help + "\n" if self.script_help else "",
                    *(
                        _section(template.title, template.description, template.table())
                        for template in templates
                    ),
                ],
            )
        )
