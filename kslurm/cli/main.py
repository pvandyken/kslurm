from __future__ import absolute_import

import attr

from kslurm.args import TailArg
from kslurm.args.arg_types import SubCommand
from kslurm.args.command import command
from kslurm.cli import kbatch, kjupyter, kpy, krun
from kslurm.cli.config import config
from kslurm.installer import install

NAME = "kslurm"
HOME_DIR = "KSLURM_HOME"
ENTRYPOINTS = ["kbatch", "krun", "kjupyter", "kslurm", "kpy"]


@attr.s(auto_attribs=True)
class KslurmModel:
    command: SubCommand = SubCommand(
        commands={
            "kbatch": kbatch,
            "krun": krun,
            "kjupyter": kjupyter,
            "kpy": kpy,
            "config": config,
            "update": lambda x: None,  # type: ignore
        },
    )

    tail: TailArg = TailArg("Args")


@command
def main(args: KslurmModel) -> None:
    command = args.command.value
    tail = args.tail
    name = f"kslurm {args.command.raw_value}"
    if args.command.raw_value == "update":
        install(tail.values, NAME, HOME_DIR, ENTRYPOINTS)
    command([name, *tail.values])


if __name__ == "__main__":
    main(["kslurm", "kbatch", "-h"])
