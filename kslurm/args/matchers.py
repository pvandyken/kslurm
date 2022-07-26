from __future__ import absolute_import

import abc
import re
from pathlib import Path
from typing import Any, Callable, Literal, Optional, overload

import attrs

from kslurm.args.arg import Context, Parser


class BasicMatcher(abc.ABC):
    duplicates: bool = False
    max_len: Optional[int] = None

    def __call__(self, arg: str, param: Parser[Any], context: Context):
        if param.value is None and param.validation_err is None:
            return self.test(arg)
        if not self.duplicates:
            return False
        if self.max_len is not None:
            try:
                if len(param.value or "") > self.max_len:
                    return False
            except KeyError:
                pass
        return self.test(arg)

    @abc.abstractmethod
    def test(self, arg: str) -> bool:
        raise NotImplementedError()

    def settings(self, duplicates: bool = False, max_len: Optional[int] = None):
        self.duplicates = duplicates
        self.max_len = max_len
        return self


class choice(BasicMatcher):
    def __init__(self, *choices: str):
        self.choices = choices

    def test(self, arg: str):
        return arg in self.choices


@attrs.frozen
class regex(BasicMatcher):
    pattern: str

    def test(self, arg: str):
        return bool(re.match(self.pattern, arg))


@attrs.frozen
class path(BasicMatcher):
    is_dir: bool = False

    def test(self, arg: str):
        is_path = "/" in arg and Path(arg).exists()
        if self.is_dir:
            return is_path and Path(arg).is_dir()
        return is_path


class everything(BasicMatcher):
    def test(self, arg: str):
        return True


@overload
def option_chain(
    initializer: str, number: Literal[1], matcher: BasicMatcher
) -> Callable[[str, Parser[Any], Context], bool]:
    ...


@overload
def option_chain(
    initializer: str, number: Optional[int], matcher: BasicMatcher
) -> Callable[[str, Parser[list[Any]], Context], bool]:
    ...


def option_chain(initializer: str, number: Optional[int], matcher: BasicMatcher) -> Any:
    def inner_single(arg: str, _: Parser[Any], context: Context):
        if context.last_matched is not None and context.last_matched.id == initializer:
            return matcher.test(arg)
        return False

    def inner_chain(arg: str, param: Parser[list[Any]], context: Context):
        if (
            context.last_matched is not None
            and context.last_matched.id in [initializer, param.id]
            and (number is None or len(param.value or []) <= number)
        ):
            return matcher.test(arg)
        return False

    if number == 1:
        return inner_single
    else:
        return inner_chain
