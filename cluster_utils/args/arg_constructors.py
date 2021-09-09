from typing import Callable
import cluster_utils.args.arg_types as argt
import attr, abc


@attr.s(auto_attribs=True)
class ArgConstructor(abc.ABC):
    id: str
    match: Callable[[str], bool]
    format: Callable[[str], str]=lambda x: x
    default: str = ""

    @abc.abstractmethod
    def __call__(self, arg: str) -> argt.Arg:
        pass

class ShapeArgConstructor(ArgConstructor):
    def __call__(self, arg: str = ""):
        if not arg:
            arg = self.default
        return argt.ShapeArg(self.id, self.format(arg))

@attr.s(auto_attribs=True)
class KeywordArgConstructor(ArgConstructor):
    num: int = 1
    validator: Callable[[str], str]=lambda x: x

    def __call__(self, arg: str = ""):
        if not arg:
            arg = self.default
        return argt.KeywordArg(self.id, self.format(arg), self.num, self.validator)
        
    