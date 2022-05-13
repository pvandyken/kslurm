from __future__ import absolute_import

import importlib.resources as impr
import os
import shutil
import subprocess as sp
import tarfile
from pathlib import Path
from typing import Any, Optional

import attrs
import requests

from kslurm.appcache import Cache
from kslurm.appconfig import Config
from kslurm.args import CommandError, command, positional
from kslurm.args.arg_types import Subcommand
from kslurm.args.arg_types_cast import flag, keyword, subcommand
from kslurm.cli.krun import krun
from kslurm.container import Container
from kslurm.exceptions import ValidationError
from kslurm.models import validators
from kslurm.utils import get_hash


class SingularityDirError(CommandError):
    pass


class SingularityDir(type(Path())):
    def __new__(cls):
        pipdir = Path(Config()["pipdir"])
        pipdir.mkdir(exist_ok=True)
        singularity_dir = pipdir / "containers"
        singularity_dir.mkdir(exist_ok=True)
        return super().__new__(cls, singularity_dir)

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.work.mkdir(exist_ok=True)
        self.images.mkdir(exist_ok=True)
        self.uris.mkdir(exist_ok=True)
        self.snakemake.mkdir(exist_ok=True)
        self.aliases.mkdir(exist_ok=True)

    @property
    def work(self):
        return self / "work"

    @property
    def images(self):
        return self / "images"

    @property
    def uris(self):
        return self / "uris"

    @property
    def snakemake(self):
        return self / "snakemake"

    @property
    def aliases(self):
        return self / "aliases"

    def get_data_path(self, container: Container):
        if container.cache_path:
            return self.images / container.cache_path
        result = self.uris / container.uri_path
        result.parent.mkdir(parents=True, exist_ok=True)
        return result

    def has_container(self, container: Container):
        if container.cache_path:
            return (self.images / container.cache_path).exists()
        return (self.uris / container.uri_path).exists()

    def update_uri_link(self, container: Container):
        if container.cache_path:
            if (cache_path := self.images / container.cache_path).exists():
                uri_path = self.uris / container.uri_path
                if uri_path.exists():
                    if not uri_path.is_symlink():
                        os.remove(uri_path)
                    elif cache_path.samefile(os.readlink(uri_path)):
                        return False
                    else:
                        os.unlink(uri_path)
                uri_path.symlink_to(cache_path)
                return True
            raise ValueError()
        return False


class AliasError(CommandError):
    pass


@attrs.define
class ContainerAlias:
    alias: str
    singularity_dir: SingularityDir
    _image: Optional[Container] = None

    def __attrs_post_init__(self):
        self.path.parent.mkdir(exist_ok=True)
        if self.path.exists():
            if not self.path.is_symlink():
                raise AliasError(
                    f"File or directory found at alias path '{self.path}'. Please "
                    "manually move or remove this item."
                )
            try:
                self.image
            except ValueError:
                raise AliasError(
                    f"Symlink found at '{self.path}' that does not currently point to "
                    "a kapp-controlled image. Please manually move or remove this item."
                )

    @property
    def path(self):
        return self.singularity_dir.aliases / self.alias

    @property
    def image(self):
        if self._image is None:
            self._image = Container.from_uri_path(
                Path(os.readlink(self.path)).relative_to(
                    self.singularity_dir / "images"
                )
            )
        return self._image

    def __bool__(self) -> bool:
        return self.path.exists()

    def check_upgrade(self, new_app: Container):
        if not self.image.is_same_container(new_app):
            raise AliasError(
                f"Alias '{self.alias}' is currently pointing to '{self.image.uri}'. To "
                "change this alias, run again with -f"
            )

    def link(self, app: Container):
        if self.path.exists():
            if app == self.image:
                print(f"Alias '{self.alias}' already set to '{app}'")
                return
            print(f"Updating alias '{self.alias}' from {self.image} to {app}")
            self.path.unlink()
        else:
            print(f"Aliasing {app} as {self.alias}")
        self.path.symlink_to(self.singularity_dir.images / app.uri_path)
        self._image = None


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
def _path(uri_or_alias: str = positional()):
    singularity_dir = SingularityDir()
    try:
        validators.fs_name(uri_or_alias)
    except ValidationError:
        container = None
    else:
        # Is it in the alias directory
        if (singularity_dir.aliases / uri_or_alias).exists():
            container = ContainerAlias(uri_or_alias, singularity_dir).image
        else:
            container = None

    if container is None:
        # Does it look like a uri
        try:
            container = Container.from_uri(uri_or_alias)
        except ValueError:
            print(
                f"Invalid identifier '{uri_or_alias}'. Must be either an alias for a "
                "container, or a valid container uri: "
                "'<scheme>://[<org>/]<image>[:<tag>]"
            )
            return 1

    print(singularity_dir.get_data_path(container))


@attrs.frozen
class _KappModel:
    command: Subcommand = subcommand(
        commands={
            "pull": _pull.cli,
            "path": _path.cli,
        },
    )


@command
def kapp(cmd_name: str, args: _KappModel, tail: list[str]):
    """Set of commands for interacting with python virtual envs"""
    name, func = args.command
    entry = f"{cmd_name} {name}"
    return func([entry, *tail])
