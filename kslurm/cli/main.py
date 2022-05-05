from __future__ import absolute_import

import importlib.resources as impr
from pathlib import Path

import attr

import neuroglia_helpers
from kslurm.args import Subcommand, flag, subcommand
from kslurm.args.command import command
from kslurm.cli import kbatch, kjupyter, kpy, krun
from kslurm.cli.config import config
from kslurm.installer.installer import install

NAME = "kslurm"
HOME_DIR = "KSLURM_HOME"
ENTRYPOINTS = ["kbatch", "krun", "kjupyter", "kslurm", "kpy"]


@command(typer=True)
def _neuroglia_helpers(show_src: bool = flag(["--src-dir"])):
    if show_src:
        print(Path(neuroglia_helpers.__file__).parent)
    else:
        with impr.path("kslurm.bin", "neuroglia-helpers.sh") as path:
            print(f"\nsource {path.resolve()}")


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
            "neuroglia-helpers": _neuroglia_helpers,
        },
    )


@command
def main(args: KslurmModel, tail: list[str]) -> int:
    name, func = args.command
    entry = f"kslurm {name}"
    if name == "update":
        install(tail, NAME, HOME_DIR, ENTRYPOINTS)
    return func([entry, *tail])


if __name__ == "__main__":
    main(["kslurm", "kbatch", "-h"])
