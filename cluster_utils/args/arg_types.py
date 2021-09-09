from __future__ import annotations
from typing import Callable, Generic, Iterable, List, TypeVar, Union
import  abc
import copy
from colorama import Fore, Style

from cluster_utils.exceptions import CommandLineError, ValidationError

T = TypeVar("T")

class Arg(abc.ABC, Generic[T]):
    def __init__(self, *,
            id: str = "",
            match: Callable[[str], bool],
            value: Union[None, T] = None,
            format: Callable[[str], T]=str):
        self.id = id
        self.match = match
        self._value = value
        self._format = format

    @property
    def value(self):
        if self._value is None:
            raise Exception()
        return self._value
        

    @value.setter
    def value(self, value: Union[None, T]):
        self._value = value

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
            value: Union[None, T] = None, 
            id: str="positional",
            format: Callable[[str], T]=str,
            validator: Callable[[str], str] = lambda x: x,
            updated: bool = False):
        super().__init__(id=id, match=lambda x: True, value=value, format=format)
        self.validator = validator
        self.updated = updated

    @property
    def value(self):
        if self._value is None:
            raise Exception()
        return self._value

    @value.setter
    def value(self, value: Union[None, T]):
        self._value = value


    def set_value(self, value: str):
        try:
            return PositionalArg[T](
                id=self.id,
                value = self._format(self.validator(value)),
                format = self._format,
                validator = self.validator,
                updated = True)
        except ValidationError as err:
            raise CommandLineError(f"""
    {Fore.RED + Style.BRIGHT}ERROR:{Style.RESET_ALL}
        Invalid value for "{Style.BRIGHT + self.id + Style.RESET_ALL}":
            {err.msg}
            """, err)


class ShapeArg(Arg[T]):
    def __init__(self,*,
            id: str = "", 
            match: Callable[[str], bool],
            value: Union[None, T] = None,
            format: Callable[[str], T]=str,
            updated: bool = False):
        super().__init__(id=id, match=match, value=value, format=format)
        self.updated = updated

    def set_value(self, value: str):
        return ShapeArg[T](
            id=self.id,
            format = self._format,
            value = self._format(value),
            match = self.match,
            updated = True)

class FlagArg(Arg[bool]):
    def __init__(self, *,
            id: str = "",
            match: List[str],
            value: bool = False):

        def check_match(val: str):
            if val in match:
                return True
            return False
        
        super().__init__(id=id, match=check_match, format=bool)
        self._value = value
        self.match_list = match


    def set_value(self, value: str):
        return FlagArg(
            id=self.id,
            value = self._format(value),
            match = self.match_list)


S = TypeVar("S")

class KeywordArg(Arg[bool], Generic[S]):
    def __init__(self, *,
            id: str = "",
            match: Callable[[str], bool],
            value: bool = False,
            num: int = 1,
            validate: Callable[[str], str] = lambda x: x,
            err_message: str = "",
            values: List[str] = []):
        super().__init__(id=id, match=match, format=bool)
        self._value = value
        self.num = num
        self.validate = validate
        self.values = values
        self.err_message = err_message

    @property
    def values(self) -> List[str]:
        return self._values
    
    @values.setter
    def values(self, values: List[str]):
        self._values = values
    
    def set_value(self, value: str):
        return KeywordArg[S](
            id = self.id,
            value = self._format(value),
            match = self.match,
            num = self.num,
            validate =  self.validate)

    def add_values(self, values: Iterable[str]):
        try:
            return KeywordArg[S](
                id=self.id, 
                value = self._value, 
                match=self.match,
                num=self.num, 
                validate=self.validate, 
                values=list(map(self.validate, values)))
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
    def __init__(self):
        super().__init__(id="tail", num=-1, match=lambda x: True)

