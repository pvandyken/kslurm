from __future__ import absolute_import

import importlib.resources as impr
import os
import shutil
import subprocess as sp
import tarfile
from typing import Optional

import attrs
import requests

from kslurm.appcache import Cache
from kslurm.args import command, positional
from kslurm.args.arg_types import Subcommand
from kslurm.args.arg_types_cast import flag, keyword, subcommand
from kslurm.cli.kapp.image import img_cmd
from kslurm.cli.krun import krun
from kslurm.container import Container, ContainerAlias, SingularityDir
from kslurm.models import validators
from kslurm.utils import get_hash


def _update_aliases(
    singularity_dir: SingularityDir,
    app: Container,
    uri: str,
    alias: Optional[ContainerAlias],
):
    if singularity_dir.update_uri_link(app):
        print(f"Updated '{uri}' to '{app.digest}'")
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


@command(inline=True)
def _pull(
    uri: str = positional(),
    alias_name: list[str] = keyword(
        ["-a", "--alias"],
        help="Alias for the docker container",
        validate=validators.fs_name,
    ),
    force: bool = flag(["-f", "--force"], help="Force overwriting of aliases"),
    # executable: bool = flag(
    #     ["-x", "--exe"], help="Include --name as an executable on the $PATH"
    # ),
):
    if sp.run(["command", "-v", "singularity"], capture_output=True).returncode != 0:
        print(
            "singularity command is not available. Try running `module load singularity"
        )
        return 1

    try:
        app = Container.from_uri(uri, lookup_digest=True)
    except ValueError as err:
        print(err.args[0])
        return 1
    if app.scheme != "docker":
        print(f"Invalid scheme '{app.scheme}'. Only 'docker://' uris supported")
        return 1

    singularity_dir = SingularityDir()

    if alias_name and alias_name[0]:
        alias = ContainerAlias(alias_name[0], singularity_dir)
        if alias and not force:
            alias.check_upgrade(app)
    else:
        alias = None

    if singularity_dir.has_container(app):
        _update_aliases(singularity_dir, app, uri, alias)
        return 0

    image_path = singularity_dir.get_data_path(app)

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
            print("Unable to retrieve container download script")
            return 1
        script = r.text
        hashed = impr.read_text("kslurm.data", "download_frozen_container.hash")
        if get_hash(script, method="sha512") != hashed.strip():
            print("Frozen image download script does not match hash. Cannot continue.")
            return 1
        cache[url] = script
        os.chmod(cache.get_path(url), 0o776)

    frozen_image = singularity_dir.work / get_hash(app.address)
    proc = sp.run([str(cache.get_path(url)), str(frozen_image), app.address])
    if proc.returncode != 0:
        return 1
    with tarfile.open(frozen_image.with_suffix(".tar"), "w") as tar:
        for path in frozen_image.iterdir():
            tar.add(path, arcname=path.relative_to(frozen_image))

    # Check that image_path is not a broken symlink
    if not image_path.exists() and image_path.is_symlink():
        image_path.unlink()
    krun.cli(
        [
            "krun",
            "1:00",
            "32G",
            "singularity",
            "build",
            str(image_path),
            f"docker-archive://{frozen_image.with_suffix('.tar')}",
        ]
    )
    shutil.rmtree(singularity_dir.work)

    _update_aliases(singularity_dir, app, uri, alias)


@command(inline=True)
def _path(
    uri_or_alias: str = positional(),
    quiet: bool = flag(["-q", "--quiet"], help="Don't print any errors"),
):
    singularity_dir = SingularityDir()
    try:
        container = singularity_dir.find(uri_or_alias)
    except Exception as err:
        if not quiet:
            raise err
        return 1

    if container is None:
        print(f"No image with identifier '{uri_or_alias}' found")
        return 1
    print(singularity_dir.get_data_path(container))


@attrs.frozen
class _KappModel:
    command: Subcommand = subcommand(
        commands={
            "pull": _pull.cli,
            "path": _path.cli,
            "image": img_cmd.cli,
        },
    )


@command
def kapp(cmd_name: str, args: _KappModel, tail: list[str]):
    """Set of commands for interacting with containers"""
    name, func = args.command
    entry = f"{cmd_name} {name}"
    return func([entry, *tail])
