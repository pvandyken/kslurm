from __future__ import absolute_import

from typing_extensions import ParamSpec, Protocol

P = ParamSpec("P")


class WrappedCommand(Protocol):
    def __call__(self, argv: list[str] = ...) -> int:
        ...
