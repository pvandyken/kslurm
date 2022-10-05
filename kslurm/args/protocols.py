from __future__ import absolute_import, annotations

from typing import Generic

from typing_extensions import ParamSpec, Protocol

from kslurm.args.help import HelpText

P = ParamSpec("P")


class WrappedCommand(Protocol):
    def __call__(self, argv: list[str] = ...) -> int:
        ...


class Command(Protocol, Generic[P]):
    def get_helptext(self, entrypoint: str) -> HelpText:
        ...

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> int:
        ...

    def cli(self, argv: list[str] = ...) -> int:
        ...
