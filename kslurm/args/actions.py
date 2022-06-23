from __future__ import absolute_import

from typing import Any, Callable, Generic, Optional, TypeVar

import attrs
from typing_extensions import Self

from kslurm.args.arg import Context, Parser

T = TypeVar("T")


class NO_FORMAT:
    def __new__(cls, arg: Any, __: Any, ___: Any):
        return arg


class NO_CONVERT:
    def __new__(cls, arg: Any):
        return arg


@attrs.define
class Action(Generic[T]):
    formatter: Callable[[str, Parser[Any], Context], T] = NO_FORMAT
    validator: Optional[Callable[[str, Parser[Any], Context], None]] = None

    @property
    def has_formatter(self):
        return self.formatter is not NO_FORMAT and self.formatter is not NO_CONVERT

    def with_converter(self, _converter: Callable[[str], Any], /) -> Self:
        return self.convert(_converter)

    def convert(self, converter: Callable[[str], T]) -> Self:
        return convert(converter, self)

    def format(self, formatter: Callable[[str, Parser[T], Context], T]) -> Self:
        return format(formatter, self)

    def validate(self, validator: Callable[[str], None]) -> Self:
        return validate(validator, self)

    def replace(self):
        return replace(formatter=self.formatter, validator=self.validator)

    def append(self):
        return append(formatter=self.formatter, validator=self.validator)

    def raises(self, error: Exception):
        return raises(error=error, validator=self.validator)


class replace(Action[T]):
    def __call__(self, arg: str, parser: Parser[Any], context: Context):
        if self.validator is not None:
            self.validator(arg, parser, context)
        return self.formatter(arg, parser, context)


class append(Action[T]):
    def __call__(self, arg: str, parser: Parser[list[Any]], context: Context):
        if self.validator is not None:
            self.validator(arg, parser, context)
        curr_value = parser.value or []
        return curr_value + [self.formatter(arg, parser, context)]


@attrs.define
class raises:
    error: Exception
    validator: Optional[Callable[[str, Parser[Any], Context], None]] = None

    @property
    def has_formatter(self):
        return True

    def with_converter(self, _converter: Callable[[str], Any], /) -> Self:
        raise NotImplementedError()

    def __call__(self, arg: str, parser: Parser[Any], context: Context):
        if self.validator is not None:
            self.validator(arg, parser, context)
        raise self.error


def convert(converter: Callable[[str], T], template: Optional[Action[T]] = None):
    def formatter(arg: str, _: Any, __: Any):
        return converter(arg)

    newformatter = NO_FORMAT if converter is NO_CONVERT else formatter

    return format(newformatter, template)


def format(
    formatter: Callable[[str, Parser[T], Context], T],
    template: Optional[Action[T]] = None,
):
    if template is not None:
        template.formatter = formatter
    else:
        template = Action(formatter=formatter, validator=None)
    return template


def validate(
    validator: Callable[[str], None],
    template: Optional[Action[T]] = None,
) -> Action[T]:
    def _validator(arg: str, _: Any, __: Any):
        validator(arg)

    if template is not None:
        template.validator = _validator
    else:
        template = Action(validator=_validator)
    return template
