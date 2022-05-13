from __future__ import absolute_import

from typing import Any, Generic, List, overload

from typing_extensions import ParamSpec, Protocol

P = ParamSpec("P")


class WrappedCommand(Protocol):
    def __call__(self, argv: List[str] = ...) -> int:
        ...


class TransparentWrappedCommand(Protocol, Generic[P]):
    @overload
    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> int:
        ...

    @overload
    def __call__(self, argv: list[str] = ...) -> int:
        ...

    def __call__(self, *args: Any, **kwargs: Any) -> int:
        ...
