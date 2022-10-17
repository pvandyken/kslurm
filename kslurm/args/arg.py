from __future__ import absolute_import, annotations

import abc
import textwrap as txt
from typing import (
    Any,
    Callable,
    DefaultDict,
    Generic,
    Literal,
    Optional,
    Protocol,
    TypeVar,
    Union,
    overload,
)

import attr
from colorama import Fore, Style
from rich.table import Table
from rich.text import Text
from typing_extensions import Self

from kslurm.exceptions import CommandLineError, MandatoryArgError, ValidationError

T = TypeVar("T")
S = TypeVar("S")

HelpRow = Union[list[Union[Text, str]], list[Text], list[str]]


class _SkipHelp:
    """
    Sentinel class to indicate argument should not be shown in help messages

    ``_SkipHelp`` is a singleton. There is only ever one of it.

    """

    _singleton = None

    def __new__(cls):
        if _SkipHelp._singleton is None:
            _SkipHelp._singleton = super(_SkipHelp, cls).__new__(cls)
        return _SkipHelp._singleton

    def __repr__(self):
        return "SKIPHELP"

    def __bool__(self):
        return False

    def __len__(self):
        return 0  # __bool__ for Python 2

    pass


SKIPHELP: Any = _SkipHelp()


def _mandatoryarg_err(
    label: str,
    help: str | None = None,
    help_template: AbstractHelpTemplate | None = None,
):
    _h = help or help_template.help if help_template else None
    return MandatoryArgError(
        f"{Fore.RED + Style.BRIGHT}ERROR:{Style.RESET_ALL}\n"
        + txt.indent(
            f"{Style.BRIGHT}'{label}'{Style.RESET_ALL} has not been "
            "provided a value.\n",
            "    ",
        )
        + (
            f"{Fore.CYAN + Style.BRIGHT}HELP:{Style.RESET_ALL}\n"
            + txt.indent(f"{_h}", "    ")
            if _h
            else ""
        )
    )


class AbstractHelpTemplate(abc.ABC):
    title: str
    description: str | None = None
    header: list[str]
    cls_usage: str = ""
    rows: dict[str, list[HelpRow]] = DefaultDict(list)
    priority: int = 0
    right_align_cols: int = 1

    def usage(self, name: str, help: str, default: Optional[str]) -> str:
        raise NotImplementedError()

    @abc.abstractmethod
    def update_meta(self, **kwargs: Any) -> Self:
        ...

    @abc.abstractmethod
    def row(
        self, name: str, help: str, default: Optional[str]
    ) -> Union[list[HelpRow], HelpRow, None]:
        ...

    @abc.abstractproperty
    def help(self) -> str:
        ...

    def add_row(self, name: str, help: str, default: Optional[str]) -> None:
        new_row = self.row(name, help, default)
        if new_row:
            if all([isinstance(row, list) for row in new_row]):
                self.rows[self.__class__.__name__].extend(new_row)  # type: ignore
            elif all([not isinstance(row, list) for row in new_row]):
                self.rows[self.__class__.__name__].append(new_row)  # type: ignore
            else:
                raise TypeError(
                    f"row() in {self} must not return mixture of lists and items"
                )

    @classmethod
    def table(cls):
        t = Table.grid(padding=(0, 2), expand=True)
        for _ in range(cls.right_align_cols):
            t.add_column(justify="right", no_wrap=True)
        if cls.header:
            t.add_row(*cls.header, style="bold")
        for r in cls.rows[cls.__name__]:
            t.add_row(*list(r))
        return t


@attr.frozen
class Context:
    args: list[str]
    current_arg: int
    params: dict[str, Parser[Any]]
    last_matched: Optional[Parser[Any]]


class ActionProtocol(Generic[T], Protocol):
    @property
    def has_formatter(self) -> bool:
        ...

    def with_converter(self, _converter: Callable[[str], T], /) -> Self:
        ...

    def __call__(self, arg: str, parser: Parser[Any], context: Context) -> T:
        ...


@attr.frozen
class Parser(Generic[T]):
    priority: int
    match: Callable[[str, Self, Context], Union[bool, str]]
    action: ActionProtocol[T]
    id: str = ""
    terminal: bool = False
    value: Optional[T] = None
    raw_value: list[str] = []
    validation_err: Optional[ValidationError] = None

    def with_id(self, id: str):
        return attr.evolve(self, id=id)

    def with_value(self, value: Optional[str], context: Context):
        if value is None:
            return attr.evolve(self, value=value, values=[])

        try:
            return attr.evolve(
                self,
                value=self.action(value, self, context),
                raw_value=self.raw_value + [value],
            )
        except ValidationError as err:
            return attr.evolve(
                self,
                validation_err=ValidationError(
                    f"""{Fore.RED + Style.BRIGHT}ERROR:{Style.RESET_ALL}
    Invalid value for "{Style.BRIGHT}{{label}}{Style.RESET_ALL}": {err.msg}"""
                ),
            )

    def __repr__(self) -> str:
        # values_repr =
        # " : '" + "', '".join(map(str, self.values)) if self.values else ""
        return f"<{self.__class__.__name__}: '{self.id}' = {self.value}'>"


@attr.frozen
class ParamInterface(abc.ABC, Generic[T]):
    id: str
    name: str

    @property
    @abc.abstractmethod
    def value(self) -> T:
        ...

    @abc.abstractmethod
    def get_parsers(self) -> dict[str, Parser[Any]]:
        ...

    @abc.abstractmethod
    @overload
    def read_parsers(
        self,
        parsers: dict[str, Parser[Any]],
        raw_values: Literal[False] = ...,
        updated: Literal[False] = ...,
    ) -> tuple[dict[str, Any], dict[str, CommandLineError]]:
        ...

    @abc.abstractmethod
    @overload
    def read_parsers(
        self,
        parsers: dict[str, Parser[Any]],
        raw_values: Literal[True] = ...,
        updated: Literal[False] = ...,
    ) -> tuple[dict[str, Any], dict[str, CommandLineError], dict[str, list[str]]]:
        ...

    @abc.abstractmethod
    @overload
    def read_parsers(
        self,
        parsers: dict[str, Parser[Any]],
        raw_values: Literal[False] = ...,
        updated: Literal[True] = ...,
    ) -> tuple[dict[str, Any], dict[str, CommandLineError], dict[str, bool]]:
        ...

    @abc.abstractmethod
    @overload
    def read_parsers(
        self,
        parsers: dict[str, Parser[Any]],
        raw_values: Literal[True] = ...,
        updated: Literal[True] = ...,
    ) -> tuple[
        dict[str, Any],
        dict[str, CommandLineError],
        dict[str, list[str]],
        dict[str, bool],
    ]:
        ...

    @abc.abstractmethod
    @overload
    def read_parsers(
        self,
        parsers: dict[str, Parser[Any]],
        raw_values: bool = ...,
        updated: bool = ...,
    ) -> tuple[dict[str, Any], ...]:
        ...

    @abc.abstractmethod
    def read_parsers(
        self,
        parsers: Any,
        raw_values: Any = False,
        updated: Any = False,
    ) -> Any:
        ...

    def _get_parser_extras(
        self,
        parsers: dict[str, Parser[Any]],
        raw_values: bool,
        updated: bool,
    ) -> Any:
        raw_vals = (
            [{id: parser.raw_value for id, parser in parsers.items()}]
            if raw_values
            else []
        )
        updated_vals = (
            [{id: parser.value is not None for id, parser in parsers.items()}]
            if updated
            else []
        )
        return (*raw_vals, *updated_vals)

    @property
    def label(self) -> str:
        if not self.name:
            return self.id
        return self.name


class SimpleParsable(abc.ABC, Generic[T]):
    @property
    @abc.abstractmethod
    def primary_parser(self) -> Parser[T]:
        ...

    @abc.abstractmethod
    def with_primary_parser(self, parser: Parser[T]) -> Self:
        ...


class Helpable(abc.ABC):
    help: str
    help_template: Optional[AbstractHelpTemplate]


@attr.frozen(eq=False)
class Arg(ParamInterface[T], SimpleParsable[T], Helpable):
    parser: Parser[T]
    default: Optional[T] = None
    id: str = ""
    raw_value: list[str] = []
    help: str = ""
    help_template: Optional[AbstractHelpTemplate] = None
    name: str = ""
    optional: bool = False

    _value: Optional[T] = None

    @property
    def value(self) -> T:
        if self._value is not None:
            return self._value

        if self.default is not None:
            return self.default

        raise _mandatoryarg_err(
            self.label,
            self.help,
            self.help_template,
        )

    @property
    def assigned_value(self) -> Optional[T]:
        return self._value

    def get_parsers(self):
        return {self.id: self.parser.with_id(self.id)}

    def read_parsers(
        self,
        parsers: dict[str, Parser[Any]],
        raw_values: bool = False,
        updated: bool = False,
    ):
        parser = parsers[self.id]
        err = parser.validation_err
        if err is not None:
            err.format(label=self.label)
        if self.optional or parser.value is not None:
            value = {self.id: parser.value}

        elif self.optional:
            value = {self.id: None}

        elif self.default is not None:
            value = {self.id: self.default}
        else:
            value = {}
            err = err or _mandatoryarg_err(self.label, self.help, self.help_template)

        err_dict = {parser.id: err} if err is not None else {}
        extras = self._get_parser_extras(parsers, raw_values, updated)
        return value, err_dict, *extras

    @property
    def primary_parser(self) -> Parser[T]:
        return self.parser

    def with_primary_parser(self, parser: Parser[T]) -> Self:
        return attr.evolve(self, parser=parser)

    def __repr__(self) -> str:
        # values_repr =
        # " : '" + "', '".join(map(str, self.values)) if self.values else ""
        return f"<{self.__class__.__name__}: '{self.id}' = {self._value}'>"

    def __eq__(self, o: object) -> bool:
        if isinstance(o, self.__class__):
            return o._value == self._value and o.id == self.id
        else:
            return False

    def with_id(self, id: str):
        return attr.evolve(self, id=id)


@attr.frozen
class ParamSet(ParamInterface[T], SimpleParsable[T], Helpable):
    parent: Parser[bool]
    child: Parser[T]
    default: Optional[T] = None
    id: str = ""
    name: str = ""
    help: str = ""
    help_template: Optional[AbstractHelpTemplate] = None
    optional: bool = False

    @property
    def value(self):
        if self.child.value is not None:
            return self.child.value

        if self.default is not None:
            return self.default

        raise _mandatoryarg_err(self.label, self.help, self.help_template)

    @property
    def assigned_value(self):
        return self.child.value

    @property
    def raw_value(self):
        return self.child.raw_value

    def get_parsers(self):
        return {self.parent.id: self.parent, self.id: self.child.with_id(self.id)}

    def read_parsers(
        self,
        parsers: dict[str, Parser[Any]],
        raw_values: bool = False,
        updated: bool = False,
    ):
        child = parsers[self.id]
        err = child.validation_err
        if child.value is not None:
            value = {child.id: child.value}

        elif self.default is not None:
            value = {child.id: self.default}

        elif self.optional:
            value = {child.id: None}

        else:
            value = {}
            err = err or _mandatoryarg_err(self.label, self.help, self.help_template)

        err_dict = {child.id: err} if err is not None else {}
        extras = self._get_parser_extras(parsers, raw_values, updated)

        return value, err_dict, *extras

    @property
    def primary_parser(self) -> Parser[T]:
        return self.child

    def with_primary_parser(self, parser: Parser[T]) -> Self:
        return attr.evolve(self, child=parser)

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}: '{self.id}' = {self.assigned_value}'>"
