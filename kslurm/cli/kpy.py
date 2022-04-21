from __future__ import absolute_import

import importlib.resources as impr

import attr

from kslurm.args.arg_types import SubCommand, TailArg
from kslurm.args.command import command


@command
def _bash():
    with impr.path("kslurm.bin", "bash.sh") as path:
        print(f"\nsource {path.resolve()}")


@attr.frozen(auto_attribs=True)
class KpyModel:
    command: SubCommand = SubCommand(
        commands={
            "load": _bash,
            "save": _bash,
            "bash": _bash,
        },
    )

    tail: TailArg = TailArg("Args")


@command
def kpy(args: KpyModel) -> None:
    command = args.command.value
    tail = args.tail
    name = f"kslurm {args.command.raw_value}"
    command([name, *tail.values])
