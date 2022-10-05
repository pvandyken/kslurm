from __future__ import absolute_import

import os

import attrs

from kslurm.args import CommandError, Subcommand, command, flag, positional, subcommand
from kslurm.container import Container, SingularityDir


@command
def _list():
    """List all available containers"""
    singularity_dir = SingularityDir()
    for path in singularity_dir.iter_images():
        print(Container.from_uri_path(path.relative_to(singularity_dir.uris)))


@command(inline=True)
def _rm(
    uri_or_alias: str = positional(),
    purge: bool = flag(
        ["-p", "--purge"], help="Remove all underlying data files (not yet implemented)"
    ),
):
    """Remove a docker image uri.

    By default, only the uri pointer is removed; underlying datafiles are kept. In a
    future release, the purge flag will be available for deleting the underlying data.

    To remove datafiles, run `kapp purge dangling`
    """
    singularity_dir = SingularityDir()
    container = singularity_dir.find(uri_or_alias)
    if container is None:
        raise CommandError(f"No image with identifier '{uri_or_alias}' found")

    path = singularity_dir.uris / container.uri_path

    if not path.is_symlink() and not purge:
        raise CommandError(
            f"The uri {container.uri}' is directly attached to it's data and cannot "
            "be removed without the --purge flag."
        )

    if path.is_symlink() and purge:
        print("[INFO] The purge flag is not yet implemented in this context.")

    for snakemake_alias in singularity_dir.snakemake.iterdir():
        if snakemake_alias.is_symlink() and path.samefile(snakemake_alias):
            snakemake_alias.unlink()
            if path.is_symlink():
                snakemake_alias.symlink_to(os.readlink(path))

    for alias in singularity_dir.aliases.iterdir():
        if alias.is_symlink() and path.samefile(alias):
            alias.unlink()
            if uri_or_alias != alias.name:
                print(f"Removing alias '{alias.name}'")

    if path.is_symlink():
        path.unlink()
    else:
        os.remove(path)


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
