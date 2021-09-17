from __future__ import annotations
from typing import Callable, Generic, Iterable, List, Optional, TypeVar

import  abc, copy

from colorama import Fore, Style

from kslurm.exceptions import CommandLineError, ValidationError

T = TypeVar("T")

class Arg(abc.ABC, Generic[T]):
    raw_value: str

    def __init__(self, *,
            id: str,
            match: Callable[[str], bool],
            value: Optional[str],
            format: Callable[[str], T],
            help: str):
        self.id = id
        self.match = match
        self._format = format
        self.value = value
        self.help = help

    @property
    def value(self):
        if self._value is None:
            raise Exception()
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
            return o.value == self.value
        else:
            return False
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}: {self.id} = {self._value}>"

    def __str__(self) -> str:
        return str(self.value)

    def setid(self, id: str):
        c = copy.copy(self)
        c.id = id
        return c

    @abc.abstractmethod
    def set_value(self, value: str) -> Arg[T]:
        pass

class PositionalArg(Arg[T]):
    def __init__(self,
            value: Optional[str] = None, 
            id: str="positional",
            format: Callable[[str], T]=str,
            validator: Callable[[str], str] = lambda x: x,
            help: str = "",
            name: str = ""):
        super().__init__(id=id, match=lambda x: True, value=value, format=format, help=help)
        self.validator = validator
        self.name = name
        self.updated = False

    def set_value(self, value: str):
        try:
            c = copy.copy(self)
            c.value = self.validator(value)
            c.updated = True
            return c
        except ValidationError as err:
            raise CommandLineError(f"""
    {Fore.RED + Style.BRIGHT}ERROR:{Style.RESET_ALL}
        Invalid value for "{Style.BRIGHT + self.name + Style.RESET_ALL}":
            {err.msg}
            """, err)

class ChoiceArg(PositionalArg[T]):
    def __init__(self, *,
            value: Optional[str] = None, 
            match: List[str] ,
            id: str="positional",
            format: Callable[[str], T]=str,
            help: str = "",
            name: str = ""):

        def check_match(val: str):
            if val in match:
                return val
            choices = "\n".join([f"\t\t• {m}" for m in match])
            raise ValidationError(
                f"Please select between:\n"
                f"{choices}"
            )
        
        super().__init__(value=value, id=id, format=format, validator=check_match, help=help, name=name)

        self.match_list = match


class ShapeArg(Arg[T]):
    def __init__(self,*,
            id: str = "", 
            match: Callable[[str], bool],
            value: Optional[str] = None,
            format: Callable[[str], T]=str,
            help: str = "",
            name: str = "",
            syntax: str = "",
            examples: List[str] = []):
        super().__init__(id=id, match=match, value=value, format=format, help=help)
        self.updated = False
        self.name = name
        self.syntax = syntax
        self.examples = examples

    def set_value(self, value: str):
        c = copy.copy(self)
        c.value = value
        c.raw_value = value
        c.updated = True
        return c

class FlagArg(Arg[bool]):
    def __init__(self, *,
            id: str = "",
            match: List[str],
            value: bool = False,
            help: str = ""):

        def check_match(val: str):
            if val in match:
                return True
            return False
        if value:
            raw_value = match[0]
        else:
            raw_value = ""

        super().__init__(id=id, match=check_match, format=bool, value=raw_value, help=help)
        self.match_list = match


    def set_value(self, value: str):
        c = copy.copy(self)
        c.value = value
        return c

S = TypeVar("S")

class KeywordArg(FlagArg, Generic[S]):
    def __init__(self, *,
            id: str = "",
            match: List[str],
            value: bool = False,
            num: int = 1,
            validate: Callable[[str], str] = lambda x: x,
            values: List[str] = [],
            help: str = "",
            values_name: str = ""):
        super().__init__(id=id, match=match, help=help, value=value)
        self.num = num
        self.validate = validate
        self.values = values
        self.values_name = values_name

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
        try:
            c = copy.copy(self)
            c.values = list(map(self.validate, values))
            return c
        except ValidationError as err:
            raise CommandLineError(f"""
    {Fore.RED + Style.BRIGHT}ERROR:{Style.RESET_ALL}
        Invalid value for "{Style.BRIGHT + self.id + Style.RESET_ALL}":
            {err.msg}
            """, err) from err


    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}: {self.id} = {self.values}>"
    
    def __str__(self) -> str:
        return " ".join(self.values)

    def __eq__(self, o: object) -> bool:
        if isinstance(o, self.__class__):
            return o.value == self.value and o.values == self.values
        else:
            return False


class TailArg(KeywordArg[str]):
    def __init__(self, name: str = "Tail"):
        super().__init__(id="tail", num=-1, match=[])
        self.name = name

