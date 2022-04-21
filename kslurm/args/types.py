from __future__ import absolute_import

from typing import List

from typing_extensions import Protocol


class WrappedCommand(Protocol):
    def __call__(self, argv: List[str] = ...) -> None:
        ...
