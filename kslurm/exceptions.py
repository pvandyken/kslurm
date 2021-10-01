from __future__ import absolute_import, annotations

from typing import List, TypeVar

T = TypeVar("T", bound="CommandLineError")


class CommandLineError(Exception):
    def __init__(self, msg: str):
        super().__init__(msg)
        self.msg = msg


class ValidationError(CommandLineError):
    pass


class TailError(CommandLineError):
    pass


class MandatoryArgError(CommandLineError):
    pass


class CommandLineErrorGroup(CommandLineError):
    def __init__(self, msg: str, sub_errors: List[T] = []):
        super().__init__(msg)
        self.sub_errors = sub_errors


class TemplateError(Exception):
    def __init__(self, msg: str):
        super().__init__(msg)
        self.msg = msg
