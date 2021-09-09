from __future__ import annotations
from typing import Callable, Generic, Iterable, List, TypeVar, Union
import  abc
import copy

T = TypeVar("T")

class Arg(abc.ABC, Generic[T]):
    def __init__(self, *,
            id: str = "",
            match: Callable[[str], bool],
            value: Union[str, T] = "",
            format: Callable[[Union[str, T]], T]=str):
        self.id = id
        self.match = match
        self._value = value
        self._format = format

    @property
    def value(self):
        return self._format(self._value)

    @value.setter
    def value(self, value: str):
        self._value = value

    def __eq__(self, o: object) -> bool:
        if isinstance(o, self.__class__):
            return o.value == self.value
        else:
            return False
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}: {self.id} = {self.value}>"

    def __str__(self) -> str:
        return str(self.value)

    def setid(self, id: str):
        c = copy.copy(self)
        c.id = id
        return c

    @abc.abstractmethod
    def set_value(self, value: str) -> Arg[T]:
        pass

class PositionalArg(Arg[str]):
    def __init__(self, value: str = "", id: str="positional"):
        super().__init__(id=id, match=lambda x: True, value=value)

    def set_value(self, value: str = ""):
        if not value:
            value = self.value
        return PositionalArg(
            id=self.id,
            value = self._format(value))


class ShapeArg(Arg[T]):
    def set_value(self, value: Union[str, T] = ""):
        if not value:
            value = self._value
        return ShapeArg[T](
            id=self.id,
            format = self._format,
            value = value,
            match = self.match)

S = TypeVar("S")

class KeywordArg(Arg[bool], Generic[S]):
    def __init__(self, *,
            id: str = "",
            match: Callable[[str], bool],
            value: Union[str, bool] = "",
            num: int = 1,
            validate: Callable[[str], bool] = lambda x: True,
            err_message: str = "",
            values: List[str] = []):
        super().__init__(id=id, match=match, value=value, format=bool)
        self.num = num
        self.validate = validate
        self.values = values
        self.err_message = err_message

    @property
    def values(self) -> List[str]:
        return self._values
    
    @values.setter
    def values(self, values: List[str]):
        for value in values:
            if not self.validate(value):
                print("Some Error")
                exit()
        self._values = values
    
    def set_value(self, value: Union[str, bool] = ""):
        if not value:
            value = self._value
        return KeywordArg[S](
            id = self.id,
            value = value,
            match = self.match,
            num = self.num,
            validate =  self.validate)

    def add_values(self, values: Iterable[str]):
        return KeywordArg[S](
            id=self.id, 
            value = self._value, 
            match=self.match,
            num=self.num, 
            validate=self.validate, 
            values=list(values))

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

