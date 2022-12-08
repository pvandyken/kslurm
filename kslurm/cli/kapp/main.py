from __future__ import absolute_import

import importlib.resources as impr
import os
import os.path
import shutil
import subprocess as sp
import tarfile
from pathlib import Path
from typing import DefaultDict, Optional

import attrs
import requests
from InquirerPy import inquirer as inq  # type: ignore

from kslurm.appcache import Cache
from kslurm.args import (
    CommandError,
    Subcommand,
    choice,
    command,
    flag,
    keyword,
    positional,
    subcommand,
)
from kslurm.cli.kapp.alias import alias_cmd
from kslurm.cli.kapp.image import img_cmd
from kslurm.cli.krun import krun
from kslurm.container import Container, ContainerAlias, SingularityDir
from kslurm.models import formatters, validators
from kslurm.utils import get_hash

_SINGULARITY_DIR = SingularityDir()


def _update_aliases(
    singularity_dir: SingularityDir,
    app: Container,
    uri: str,
    alias: Optional[ContainerAlias],
):
    if singularity_dir.update_uri_link(app) and app.docker_data:
        print(f"Updated '{uri}' to '{app.docker_data.digest}'")
    else:
        print(f"{uri} already up to date")
    if alias is not None:
        alias.link(app)

    if (
        snakemake_path := singularity_dir.snakemake / app.snakemake_cache_path
    ).is_symlink():
        snakemake_path.unlink()
    elif snakemake_path.exists():
        os.remove(snakemake_path)
    snakemake_path.symlink_to(singularity_dir.get_data_path(app))


def _check_singularity():
    if sp.run(["command", "-v", "singularity"], capture_output=True).returncode != 0:
        raise CommandError(
            "singularity command is not available. Try running `module load singularity"
        )


@command(inline=True)
def _pull(
    uri: str = positional(),
    alias_name: str = keyword(
        ["-a", "--alias"],
        help="Alias for the docker container",
        format=validators.fs_name,
    ),
    force: bool = flag(["-f", "--force"], help="Force overwriting of aliases"),
    mem: int = keyword(
        ["--mem"],
        format=formatters.mem,
        help="Amount of memory to allocate when building image",
    )
    # executable: bool = flag(
    #     ["-x", "--exe"], help="Include --name as an executable on the $PATH"
    # ),
):
    """Pull a container. Defaults to docker hub."""
    _check_singularity()

    try:
        app = Container.from_uri(uri, lookup_digest=True)
    except ValueError as err:
        raise CommandError(err.args[0])

    if app.uri.scheme != "docker":
        raise CommandError(
            f"Invalid scheme '{app.uri.scheme}'. Only 'docker://' uris supported"
        )

    if alias_name:
        alias = ContainerAlias(alias_name, _SINGULARITY_DIR)
        if alias and not force:
            alias.check_upgrade(app)
    else:
        alias = None

    if _SINGULARITY_DIR.has_container(app):
        _update_aliases(_SINGULARITY_DIR, app, uri, alias)
        return

    if _SINGULARITY_DIR.has_raw_uri_file(app):
        if not inq.confirm(
            f"An image matching {app.uri.uri} already exists, but we can't verify if "
            "it's up to date. Would you like to pull it again?"
        ).execute():
            return


    image_path = _SINGULARITY_DIR.get_data_path(app)

    # Small images we can directly use the singularity command
    if app.docker_data and app.docker_data.size_mb < 200 and not mem:
        sp.run(["singularity", "pull", str(image_path), app.uri.uri])
        _update_aliases(_SINGULARITY_DIR, app, uri, alias)
        return

    url = (
        "https://raw.githubusercontent.com/moby/moby/v20.10.16/contrib/"
        "download-frozen-image-v2.sh"
    )
    cache = Cache()
    try:
        script = cache[url]
    except KeyError:
        r = requests.get(
            "https://raw.githubusercontent.com/moby/moby/master/contrib/"
            "download-frozen-image-v2.sh",
            headers={"user-agent": "kslurm"},
        )

        if r.status_code >= 400:
            raise CommandError("Unable to retrieve container download script")
        script = r.text
        # hashed = impr.read_text("kslurm.data", "download_frozen_container.hash")
        # if get_hash(script, method="sha512") != hashed.strip():
        #     raise CommandError(
        #         "Frozen image download script does not match hash. Cannot continue."
        #     )
        cache[url] = script
        os.chmod(cache.get_path(url), 0o776)

    frozen_image = _SINGULARITY_DIR.work / get_hash(app.uri.address)
    proc = sp.run(
        [
            str(cache.get_path(url)),
            str(frozen_image),
            (app.friendly_uri or app.uri).address,
        ]
    )
    if proc.returncode != 0:
        return 1
    with tarfile.open(frozen_image.with_suffix(".tar"), "w") as tar:
        for path in frozen_image.iterdir():
            tar.add(path, arcname=path.relative_to(frozen_image))

    # Check that image_path is not a broken symlink
    if not image_path.exists() and image_path.is_symlink():
        image_path.unlink()
    mem = (
        mem
        if mem
        else (min(64000, app.docker_data.size_mb * 20) if app.docker_data else 8000)
    )
    ret = krun.cli(
        [
            "krun",
            "1:00",
            f"{mem}M",
            "singularity",
            "build",
            "--disable-cache",
            str(image_path),
            f"docker-archive://{frozen_image.with_suffix('.tar')}",
        ]
    )
    if ret == 0:
        shutil.rmtree(_SINGULARITY_DIR.work)

        _update_aliases(_SINGULARITY_DIR, app, uri, alias)
    return ret


@command(inline=True)
def _path(
    uri_or_alias: str = positional(),
    quiet: bool = flag(["-q", "--quiet"], help="Don't print any errors"),
):
    """Print the path of the given uri or alias"""
    try:
        container = _SINGULARITY_DIR.find(uri_or_alias)
    except Exception as err:
        if not quiet:
            raise err
        return 1

    if container is None:
        raise CommandError(f"No image with identifier '{uri_or_alias}' found")
    print(_SINGULARITY_DIR.get_data_path(container))


@attrs.frozen
class _RunModel:
    container: Container = positional(
        format=_SINGULARITY_DIR.find_formatter, name="uri_or_alias"
    )


def _generic_run(container: Container, cmd: str, args: list[str]):
    _check_singularity()
    sp.run(
        [
            "singularity",
            cmd,
            _SINGULARITY_DIR.get_data_path(container),
            *args,
        ]
    )


@command
def _run(args: _RunModel, container_args: list[str]):
    _generic_run(args.container, "run", container_args)


@command
def _shell(args: _RunModel, container_args: list[str]):
    _generic_run(args.container, "shell", container_args)


@command
def _exec(args: _RunModel, container_args: list[str]):
    _generic_run(args.container, "exec", container_args)


@command(inline=True)
def _purge(
    scope: str = choice(["dangling"]),
    dry: bool = flag(
        ["-d", "--dry"],
        help="Print what files will be deleted without deleting anything",
    ),
):
    """Remove dangling containers

    Remove all containers not referred to by any uris (e.g. because the uri was removed)
    """
    uri_list = set(
        os.path.basename(os.readlink(path))
        for path in _SINGULARITY_DIR.iter_images()
        if path.is_symlink()
    )
    snakemake_aliases: dict[str, list[Path]] = DefaultDict(list)
    for path in _SINGULARITY_DIR.snakemake.iterdir():
        if path.is_symlink():
            snakemake_aliases[os.path.basename(os.readlink(path))].append(path)
    count = 0
    for file in _SINGULARITY_DIR.images.iterdir():
        if file.name in uri_list:
            continue
        if dry:
            print(file.name)
        else:
            for path in snakemake_aliases[file.name]:
                path.unlink()
            os.remove(file)
            count += 1

    if not dry:
        if not count:
            print("Nothing to remove")
        elif count == 1:
            print("Removed 1 file")
        else:
            print(f"Removed {count} files")


@command
def _snakemake():
    """Print the snakemake singularity directory (to be used with --singularity-prefix)

    Snakemake supports supplying a --singularity prefix: a directory will image files
    will be searched and saved. By supplying the path printed by this command, snakemake
    will automatically use any containers pulled using kapp
    """
    print(_SINGULARITY_DIR.snakemake.resolve())


@attrs.frozen
class _KappModel:
    command: Subcommand = subcommand(
        commands={
            "pull": _pull.cli,
            "path": _path.cli,
            "image": img_cmd.cli,
            "run": _run.cli,
            "shell": _shell.cli,
            "exec": _exec.cli,
            "alias": alias_cmd.cli,
            "purge": _purge.cli,
            "snakemake": _snakemake.cli,
        },
    )


@command
def kapp(cmd_name: str, args: _KappModel, tail: list[str]):
    """Set of commands for interacting with containers"""
    name, func = args.command
    entry = f"{cmd_name} {name}"
    return func([entry, *tail])
