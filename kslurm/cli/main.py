from __future__ import absolute_import

import attr

from kslurm.args.arg_types import Subcommand, subcommand
from kslurm.args.command import command
from kslurm.cli import kbatch, kjupyter, kpy, krun
from kslurm.cli.config import config
from kslurm.installer.installer import install

NAME = "kslurm"
HOME_DIR = "KSLURM_HOME"
ENTRYPOINTS = ["kbatch", "krun", "kjupyter", "kslurm", "kpy"]


@attr.s(auto_attribs=True)
class KslurmModel:
    command: Subcommand = subcommand(
        commands={
            "kbatch": kbatch,
            "krun": krun,
            "kjupyter": kjupyter,
            "kpy": kpy,
            "config": config,
            "update": lambda x: None,  # type: ignore
        },
    )


@command
def main(args: KslurmModel, tail: list[str]) -> None:
    name, func = args.command
    entry = f"kslurm {name}"
    if name == "update":
        install(tail, NAME, HOME_DIR, ENTRYPOINTS)
    func([entry, *tail])


if __name__ == "__main__":
    main(["kslurm", "kbatch", "-h"])
