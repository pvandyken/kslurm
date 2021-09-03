from typing import Callable, Iterable
import cluster_utils.args.arg_types as argt

class ArgConstructor:
    match: Callable[[str], bool]
    id: str
    arg: str

    def __init__(self, id: str,
                 match: Callable[[str], bool],
                 format: Callable[[str], str]=lambda x: x):
        self.id = id
        self.match = match
        self.format = format

    def __call__(self, arg: str) -> argt.Arg:
        ...

class ShapeArgConstructor(ArgConstructor):
    match: Callable[[str], bool]
    id: str
    arg: str

    def __init__(self, id: str,
                 match: Callable[[str], bool] = lambda x: True,
                 format: Callable[[str], str]=lambda x: x):
        super().__init__(id, match, format)
    
    def __call__(self, arg: str):
        return argt.ShapeArg(self.id, self.format(arg))

class KeywordArgConstructor(ArgConstructor):
    match: Callable[[str], bool]
    id: str
    arg: str

    def __init__(self, id: str,
                 match: Callable[[str], bool],
                 num: int = 0,
                 validator: Callable[[Iterable[str]], bool]=lambda x: True,
                 format: Callable[[str], str]=lambda x: x):
        super().__init__(id, match, format)
        self.validator = validator
        self.num = num

    def __call__(self, arg: str):
        return argt.KeywordArg(self.id, self.format(arg), self.num, self.validator)
        
    