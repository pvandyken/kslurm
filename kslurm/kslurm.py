from typing import List
import sys
from kslurm.args import parse_args
from kslurm.models import KslurmModel
from kslurm.submission import kjupyter, krun, kbatch
from kslurm.installer import update

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
        update(tail.values)

def main():
    kslurm(sys.argv[0], sys.argv[1:])

if __name__ == "__main__":
    main()