from __future__ import absolute_import, annotations

import itertools as it
from typing import Any, Optional, Union

import attr
import docstring_parser as doc
import more_itertools as itx
from rich.text import Text
from tabulate import tabulate
from typing_extensions import Self

from kslurm.args.arg import AbstractHelpTemplate, HelpRow
from kslurm.args.protocols import WrappedCommand


@attr.frozen
class ShapeArg(AbstractHelpTemplate):
    title = "Shape Args"
    header = ["", "Syntax", "", "Examples", "Default", ""]
    right_align_cols = 2

    syntax: str
    examples: list[str]

    def _syntax_format(self, syntax: str):
        return Text.assemble(
            *itx.interleave(
                [Text(line.strip(), style="cyan bold") for line in syntax.split(" | ")],
                it.repeat("\n"),
            )
        )

    def update_meta(self, **kwargs: Any) -> Self:
        return attr.evolve(self, **kwargs)

    def usage(self, name: str, help: str, default: Optional[str]) -> str:
        return rf"[hot]\[{name}][/]"

    def row(self, name: str, help: str, default: Optional[str]):
        return [
            Text(name, style="bold"),
            self._syntax_format(self.syntax),
            ("➔" if self.examples else ""),
            Text("\n".join(itx.always_iterable(self.examples))),
            Text(str(default), style="default_col") if default is not None else "",
            Text(help),
        ]

    @property
    def help(self):
        return ""


@attr.frozen
class PositionalArg(AbstractHelpTemplate):
    title = "Positional Args"
    header = []

    def usage(self, name: str, help: str, default: Optional[str]) -> str:
        if default is None:
            return f"[cyan]{name}[/]"
        return rf"[cyan]\[{name}][/]"

    def update_meta(self, **kwargs: Any) -> Self:
        raise NotImplementedError()

    def row(self, name: str, help: str, default: Optional[str]):
        return [
            Text(name, style="bold"),
            Text(default if default is not None else "REQUIRED", style="default_col"),
            Text(help),
        ]

    @property
    def help(self):
        return ""


@attr.frozen
class SubcommandTemplate(AbstractHelpTemplate):
    title = "Commands"
    description = "Run any command followed by -h for more information"
    header = []

    commands: dict[str, WrappedCommand]

    def usage(self, name: str, help: str, default: Optional[str]) -> str:
        return f"[cyan]{name}[/]"

    def update_meta(self, **kwargs: Any) -> Self:
        raise NotImplementedError()

    def row(
        self, name: str, help: str, default: Optional[str]
    ) -> Union[list[HelpRow], HelpRow]:
        return [
            [],
            *self.command_list,
        ]

    @property
    def command_list(self):
        return (
            [
                name,
                doc.parse(func.__doc__ or "").short_description or "",
            ]
            for name, func in self.commands.items()
        )

    @property
    def help(self):
        return tabulate(list(self.command_list), tablefmt="plain")
        # t = Table.grid(padding=(0, 2), expand=True)
        # for _ in range(2):
        #     t.add_column(justify="right", no_wrap=True)
        # for r in self.command_list:
        #     t.add_row(*r)
        # return t


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
