from __future__ import absolute_import

import os

import attrs

from kslurm.args import CommandError, Subcommand, command, positional, subcommand
from kslurm.container import SingularityDir


@command
def _list():
    """List all available aliases"""
    singularity_dir = SingularityDir()
    for alias in singularity_dir.aliases.iterdir():
        container = singularity_dir.find(alias.name) or "-INVALID-"
        print(f"{alias.name} -> {container}")


@command(inline=True)
def _rm(
    alias: str = positional(),
):
    """Remove an alias"""
    singularity_dir = SingularityDir()
    path = singularity_dir.aliases / alias
    if not path.exists():
        raise CommandError(f"'{alias}' is not a valid alias")
        return 1
    if path.is_symlink():
        path.unlink()
    elif path.exists():
        os.remove(path)


@attrs.frozen
class _AliasModel:
    command: Subcommand = subcommand(
        commands={
            "list": _list.cli,
            "rm": _rm.cli,
        },
    )


@command
def alias_cmd(cmd_name: str, args: _AliasModel, tail: list[str]):
    """Interact with container image files"""
    name, func = args.command
    entry = f"{cmd_name} {name}"
    return func([entry, *tail])
