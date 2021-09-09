from __future__ import annotations
from typing import Callable, Iterable, List
import  abc
import copy


class Arg(abc.ABC):
    def __init__(self, *,
            id: str = "",
            match: Callable[[str], bool],
            value: str = "",
            format: Callable[[str], str]=lambda x: x):
        self.id = id
        self.match = match
        self._value = value
        self.format = format

    @property
    def value(self):
        return self.format(self._value)

    def __eq__(self, o: object) -> bool:
        if isinstance(o, self.__class__):
            return o.value == self.value
        else:
            return False
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}: {self.id} = {self.value}>"

    def __str__(self) -> str:
        return self.value

    def setid(self, id: str):
        c = copy.copy(self)
        c.id = id
        return c

    @abc.abstractmethod
    def set_value(self, value: str) -> Arg:
        pass

class PositionalArg(Arg):
    def __init__(self, id: str="positional", value: str = ""):
        super().__init__(id=id, match=lambda x: True, value=value)

    def set_value(self, value: str = ""):
        if not value:
            value = self.value
        return PositionalArg(
            id=self.id,
            value = self.format(value))


class ShapeArg(Arg):
    def set_value(self, value: str = ""):
        if not value:
            value = self.value
        return ShapeArg(
            id=self.id,
            format = self.format,
            value = self.format(value),
            match = self.match)


class KeywordArg(Arg):
    def __init__(self, *,
            id: str = "",
            match: Callable[[str], bool],
            value: str = "",
            format: Callable[[str], str]=lambda x: x,
            num: int = 1,
            validate: Callable[[str], str] = lambda x: x,
            values: List[str] = []):
        super().__init__(id=id, match=match, value=value, format=format)
        self.num = num
        self.validate = validate
        self.values = values

    
    def set_value(self, value: str = ""):
        if not value:
            value = self.value
        return KeywordArg(
            id = self.id,
            value = self.format(value),
            match = self.match,
            format =  self.format, 
            num = self.num,
            validate =  self.validate)

    def add_values(self, values: Iterable[str]):
        return KeywordArg(
            id=self.id, 
            value = self.value, 
            match=self.match,
            num=self.num, 
            validate=self.validate, 
            values=[self.validate(value) for value in values])

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}: {self.id} = {self.values}>"
    
    def __str__(self) -> str:
        return " ".join(self.values)

    def __eq__(self, o: object) -> bool:
        if isinstance(o, self.__class__):
            return o.value == self.value and o.values == self.values
        else:
            return False


class TailArg(KeywordArg):
    def __init__(self):
        super().__init__(id="tail", num=-1, match=lambda x: True)

