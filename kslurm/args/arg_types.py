from __future__ import absolute_import, annotations

import abc
import copy
from typing import Callable, Generic, Iterable, List, Optional, TypeVar

from colorama import Fore, Style

from kslurm.exceptions import MandatoryArgError, ValidationError

T = TypeVar("T")
S = TypeVar("S")


class Arg(abc.ABC, Generic[T]):
    raw_value: str

    def __init__(
        self,
        *,
        id: str,
        match: Callable[[str], bool],
        value: Optional[str],
        format: Callable[[str], T],
        help: str,
    ):
        self.id = id
        self.match = match
        self._format = format
        self.value = value
        self.help = help

    @property
    def value(self):
        if self._value is None:
            raise MandatoryArgError(f"{self.name} has not been provided a value.")
        return self._value

    @value.setter
    def value(self, value: Optional[str]):
        if value is None:
            self._value = value
            self.raw_value = ""
        else:
            self._value = self._format(value)
            self.raw_value = value

    def __eq__(self, o: object) -> bool:
        if isinstance(o, self.__class__):
            return o._value == self._value
        else:
            return False

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}: {self.id} = {self._value}>"

    def __str__(self) -> str:
        return str(self.value)

    def __hash__(self) -> int:
        return hash(hash(self.id) + hash(self.value))

    def setid(self, id: str):
        c = copy.copy(self)
        c.id = id
        return c

    @property
    def name(self) -> str:
        return self.id

    @abc.abstractmethod
    def set_value(self, value: str) -> Arg[T]:
        pass


class PositionalArg(Arg[T]):
    def __init__(
        self,
        value: Optional[str] = None,
        id: str = "positional",
        format: Callable[[str], T] = str,
        validator: Callable[[str], str] = lambda x: x,
        help: str = "",
        name: str = "",
    ):
        super().__init__(
            id=id, match=lambda x: True, value=value, format=format, help=help
        )
        self.validator = validator
        self._name = name
        self.updated = False
        self.validation_err: Optional[ValidationError] = None

    def set_value(self, value: str):
        c = copy.copy(self)
        try:
            c.value = self.validator(value)
            c.updated = True
            return c
        except ValidationError as err:
            c.validation_err = ValidationError(
                f"""
    {Fore.RED + Style.BRIGHT}ERROR:{Style.RESET_ALL}
        Invalid value for "{Style.BRIGHT + self.name + Style.RESET_ALL}":
            {err.msg}
            """
            )
            return c

    @property
    def name(self):
        if self._name:
            return self._name
        return self.id


class ChoiceArg(PositionalArg[T]):
    def __init__(
        self,
        *,
        value: Optional[str] = None,
        match: List[str],
        id: str = "positional",
        format: Callable[[str], T] = str,
        help: str = "",
        name: str = "",
    ):
        def check_match(val: str):
            if val in match:
                return val
            choices = "\n".join([f"\t\t• {m}" for m in match])
            raise ValidationError(f"Please select between:\n" f"{choices}")

        super().__init__(
            value=value,
            id=id,
            format=format,
            validator=check_match,
            help=help,
            name=name,
        )

        self.match_list = match


class ShapeArg(Arg[T]):
    def __init__(
        self,
        *,
        id: str = "",
        match: Callable[[str], bool],
        value: Optional[str] = None,
        format: Callable[[str], T] = str,
        help: str = "",
        name: str = "",
        syntax: str = "",
        examples: List[str] = [],
    ):
        super().__init__(id=id, match=match, value=value, format=format, help=help)
        self.updated = False
        self._name = name
        self.syntax = syntax
        self.examples = examples

    def set_value(self, value: str):
        c = copy.copy(self)
        c.value = value
        c.raw_value = value
        c.updated = True
        return c

    @property
    def name(self):
        if self._name:
            return self._name
        return self.id


class FlagArg(Arg[bool]):
    def __init__(
        self,
        *,
        id: str = "",
        match: List[str],
        value: Optional[bool] = False,
        help: str = "",
    ):
        def check_match(val: str):
            if val in match:
                return True
            return False

        if value:
            raw_value = match[0]
        elif value is None:
            raw_value = None
        else:
            raw_value = ""

        super().__init__(
            id=id, match=check_match, format=bool, value=raw_value, help=help
        )
        self.match_list = match

    def set_value(self, value: str):
        c = copy.copy(self)
        c.value = value
        return c

    @property
    def name(self):
        return ", ".join(self.match_list)


class KeywordArg(FlagArg, Generic[S]):
    def __init__(
        self,
        *,
        id: str = "",
        match: List[str],
        value: Optional[bool] = False,
        num: int = 1,
        validate: Callable[[str], str] = lambda x: x,
        values: List[str] = [],
        help: str = "",
        values_name: str = "",
    ):
        super().__init__(id=id, match=match, help=help, value=value)
        self.num = num
        self.validate = validate
        self.values = values
        self.values_name = values_name
        self.validation_err: Optional[ValidationError] = None

    @property
    def values(self) -> List[str]:
        return self._values

    @values.setter
    def values(self, values: List[str]):
        self._values = values

    def set_value(self, value: str):
        c = copy.copy(self)
        c.value = value
        # We need to obliterate any values in order for argparse to work
        # Otherwise any default args will be included in the final list.
        # A more elegant solution would delete default args organically
        # if user-supplied args are added.
        c.values = []
        return c

    def add_values(self, values: Iterable[str]):
        c = copy.copy(self)
        try:
            c.values = list(map(self.validate, values))
            return c
        except ValidationError as err:
            c.validation_err = ValidationError(
                f"""
    {Fore.RED + Style.BRIGHT}ERROR:{Style.RESET_ALL}
        Invalid value for "{Style.BRIGHT + self.id + Style.RESET_ALL}":
            {err.msg}
            """,
            )
            return c

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}: {self.id} = {self.values}>"

    def __str__(self) -> str:
        return " ".join(self.values)

    def __eq__(self, o: object) -> bool:
        if isinstance(o, self.__class__):
            return o._value == self._value and o.values == self.values
        else:
            return False

    def __hash__(self) -> int:
        value_hash = hash(sum([hash(val) for val in self.values]))
        return hash(super().__hash__() + value_hash)


class TailArg(KeywordArg[str]):
    def __init__(self, name: str = "Tail"):
        super().__init__(id="tail", num=-1, match=[])
        self._name = name
        self.raise_exception = False

    @property
    def name(self):
        return self._name
