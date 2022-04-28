from __future__ import absolute_import, annotations

import abc
from enum import Enum, auto
from typing import (
    Callable,
    DefaultDict,
    Generic,
    Iterable,
    List,
    Optional,
    TypeVar,
    Union,
)

import attr
from colorama import Fore, Style
from rich.table import Table
from rich.text import Text

from kslurm.exceptions import MandatoryArgError, ValidationError

T = TypeVar("T")
S = TypeVar("S")

HelpRow = Union[list[Union[Text, str]], list[Text], list[str]]


class AbstractHelpEntry(abc.ABC):
    title: str
    header: list[str]

    @abc.abstractproperty
    def usage(self) -> str:
        raise NotImplementedError()

    @abc.abstractmethod
    def row(self) -> list[Union[Text, str]]:
        raise NotImplementedError()


class AbstractHelpTemplate(abc.ABC):
    title: str
    header: list[str]
    cls_usage: str = ""
    rows: dict[str, list[HelpRow]] = DefaultDict(list)
    priority: int = 0
    right_align_cols: int = 1

    def usage(self, name: str, help: str, default: Optional[str]) -> str:
        raise NotImplementedError()

    @abc.abstractmethod
    def row(
        self, name: str, help: str, default: Optional[str]
    ) -> Union[list[HelpRow], HelpRow]:
        raise NotImplementedError()

    def add_row(self, name: str, help: str, default: Optional[str]) -> None:
        new_row = self.row(name, help, default)
        if new_row and all([isinstance(row, list) for row in new_row]):
            self.rows[self.__class__.__name__].extend(new_row)  # type: ignore
        elif new_row and all([not isinstance(row, list) for row in new_row]):
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


class DuplicatePolicy(Enum):
    SKIP = auto()
    REPLACE = auto()
    APPEND = auto()


@attr.frozen(eq=False)
class Arg(Generic[T, S]):

    priority: int
    match: Callable[[str], bool]
    duplicates: DuplicatePolicy
    format: Callable[[str], T]
    id: str = ""
    raw_value: str = ""
    help: str = ""
    help_template: Optional[AbstractHelpTemplate] = None
    terminal: bool = False
    name: str = ""
    num: int = 0
    greediness: int = 0
    validate: Callable[[str], S] = lambda x: x
    values: List[S] = []
    values_name: str = ""
    validation_err: Optional[ValidationError] = None
    updated: bool = False

    _value: Optional[T] = None

    @property
    def value(self) -> T:
        if self._value is None:
            raise MandatoryArgError(f"{self.label} has not been provided a value.")
        return self._value

    @property
    def safe_value(self) -> Optional[T]:
        return self._value

    def with_value(self, value: Optional[str], updated: bool = False):
        if value is None:
            return attr.evolve(
                self, value=value, raw_value="", values=[], updated=updated
            )

        try:
            return attr.evolve(
                self,
                value=self.format(value),
                raw_value=value,
                values=[],
                updated=updated,
            )
        except ValidationError as err:
            return attr.evolve(
                self,
                updated=updated,
                validation_err=ValidationError(
                    f"""
    {Fore.RED + Style.BRIGHT}ERROR:{Style.RESET_ALL}
        Invalid value for "{Style.BRIGHT + self.label + Style.RESET_ALL}":
            {err.msg}
            """
                ),
            )

    def with_values(self, values: Iterable[str], updated: bool = False):
        try:
            return attr.evolve(
                self, values=[self.validate(value) for value in values], updated=updated
            )
        except ValidationError as err:
            return attr.evolve(
                self,
                updated=updated,
                validation_err=ValidationError(
                    f"""
    {Fore.RED + Style.BRIGHT}ERROR:{Style.RESET_ALL}
        Invalid value for "{Style.BRIGHT + self.id + Style.RESET_ALL}":
            {err.msg}
            """,
                ),
            )

    def with_err(self, err: ValidationError):
        return attr.evolve(self, validation_err=err)

    def __repr__(self) -> str:
        values_repr = " : '" + "', '".join(map(str, self.values)) if self.values else ""
        return f"<{self.__class__.__name__}: '{self.id}' = {self._value}{values_repr}'>"

    def __eq__(self, o: object) -> bool:
        if isinstance(o, self.__class__):
            return (
                o._value == self._value and o.values == self.values and o.id == self.id
            )
        else:
            return False

    def with_id(self, id: str):
        return attr.evolve(self, id=id)

    @property
    def label(self) -> str:
        if not self.name:
            return self.id
        return self.name
