from __future__ import absolute_import

import attrs

from kslurm.args import Subcommand, command, positional, subcommand
from kslurm.container import SingularityDir


@command
def _list():
    for container in SingularityDir().iter_images():
        print(container)


@command
def _rm(img: str = positional()):
    pass


@attrs.frozen
class _ImgListModel:
    command: Subcommand = subcommand(
        commands={
            "list": _list.cli,
            "rm": _rm.cli,
        },
    )


@command
def img_cmd(cmd_name: str, args: _ImgListModel, tail: list[str]):
    """Interact with container image files"""
    name, func = args.command
    entry = f"{cmd_name} {name}"
    return func([entry, *tail])
