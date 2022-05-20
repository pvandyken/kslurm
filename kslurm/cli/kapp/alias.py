from __future__ import absolute_import

import attrs

from kslurm.args import Subcommand, command, subcommand
from kslurm.container import SingularityDir


@command
def _list():
    """List all available containers"""
    singularity_dir = SingularityDir()
    for alias in singularity_dir.aliases.iterdir():
        container = singularity_dir.find(alias.name) or "-INVALID-"
        print(f"{alias.name} -> {container}")


# @command(inline=True)
# def _rm(
#     uri_or_alias: str = positional(),
# ):
#     pass


@attrs.frozen
class _AliasModel:
    command: Subcommand = subcommand(
        commands={
            "list": _list.cli,
            # "rm": _rm.cli,
        },
    )


@command
def alias_cmd(cmd_name: str, args: _AliasModel, tail: list[str]):
    """Interact with container image files"""
    name, func = args.command
    entry = f"{cmd_name} {name}"
    return func([entry, *tail])
