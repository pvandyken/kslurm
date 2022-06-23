from __future__ import absolute_import, annotations

from typing import Optional, Union

import attr
import docstring_parser as doc
from rich.text import Text

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
