
from typing import Callable, Iterable


class Arg:
    def __init__(self, id: str, arg: str):
        self.id = id
        self.arg = arg

    def __eq__(self, o: object) -> bool:
        if isinstance(o, self.__class__):
            return o.arg == self.arg
        else:
            return False
    
    def __repr__(self) -> str:
        return f"<ArgType: {self.id} = {self.arg}>"

    def __str__(self) -> str:
        return self.arg

class CommandArg(Arg):
    def __init__(self, id: str, arg: str):
        super().__init__(id, arg)

class ShapeArg(Arg):
    def __init__(self, 
                 id: str,
                 arg: str, 
                 ):
        super().__init__(id, arg)

class KeywordArg(Arg):
    def __init__(self, 
                 id: str, 
                 arg: str,
                 num: int, 
                 validate: Callable[[Iterable[str]], bool] = lambda x: True):
        super().__init__(id, arg)
        self.num = num
        self.validate = validate






