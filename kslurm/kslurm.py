from __future__ import absolute_import

import sys
from typing import List

from kslurm.args import parse_args
from kslurm.installer import install
from kslurm.models import KslurmModel
from kslurm.submission import kbatch, kjupyter, krun

NAME = "kslurm"
HOME_DIR = "KSLURM_HOME"
ENTRYPOINTS = ["kbatch", "krun", "kjupyter", "kslurm"]


def kslurm(script: str, args: List[str]) -> None:
    parsed = parse_args(sys.argv[1:], KslurmModel())
    command = parsed.command.value
    tail = parsed.tail
    if command == "krun":
        krun(command, tail.values)
    if command == "kbatch":
        kbatch(command, tail.values)
    if command == "kjupyter":
        kjupyter(command, tail.values)
    if command == "update":
        install(tail.values, NAME, HOME_DIR, ENTRYPOINTS)


def main():
    kslurm(sys.argv[0], sys.argv[1:])


if __name__ == "__main__":
    main()
