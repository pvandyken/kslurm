from __future__ import absolute_import

import attr

from kslurm.args import ChoiceArg, TailArg
from kslurm.args.command import command
from kslurm.cli.config import config
from kslurm.installer import install
from kslurm.submission import kbatch, kjupyter, krun

NAME = "kslurm"
HOME_DIR = "KSLURM_HOME"
ENTRYPOINTS = ["kbatch", "krun", "kjupyter", "kslurm"]


@attr.s(auto_attribs=True)
class KslurmModel:
    command: ChoiceArg[str] = ChoiceArg[str](
        match=["kbatch", "krun", "kjupyter", "update", "config"],
        name="Command",
        help="Run any of the commands with -h to get more information",
    )

    tail: TailArg = TailArg("Args")


@command
def kslurm(args: KslurmModel) -> None:
    command = args.command.value
    tail = args.tail
    name = f"kslurm {command}"
    if command == "krun":
        krun([name, *tail.values])
    if command == "kbatch":
        kbatch([name, *tail.values])
    if command == "kjupyter":
        kjupyter([name, *tail.values])
    if command == "update":
        install(tail.values, NAME, HOME_DIR, ENTRYPOINTS)
    if command == "config":
        config(tail.values)


if __name__ == "__main__":
    kslurm()
