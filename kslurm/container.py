from __future__ import absolute_import, annotations

import functools as ft
import operator as op
import os
import platform
import re
from pathlib import Path
from typing import Any, Optional, Union

import attrs
import requests

from kslurm.appconfig import Config
from kslurm.args.command import CommandError
from kslurm.exceptions import ValidationError
from kslurm.models import validators
from kslurm.utils import get_hash

REGISTRYBASE = "https://registry-1.docker.io"
AUTHBASE = "https://auth.docker.io"
AUTHSERVICE = "registry.docker.io"


def find_(arg: str):
    container = SingularityDir().find(arg)
    if container is None:
        raise ValidationError(f"No image with identifier '{arg}' found")
    return container


@attrs.frozen
class URI:
    scheme: str
    org: str
    repo: str
    tag: str

    URI_SCHEME = "<scheme>://[<org>/]<image>[:<tag>]"

    @classmethod
    def parse(cls, uri: str):
        if not (
            match := re.match(
                r"""
                ^(?:(?P<scheme>[^:@\/]+)\:\/\/)?
                (?:(?P<org>[^:@\/]+)\/)?
                (?P<image>[^@:\/\s]+)
                (?::(?P<tag>[^@\/]+))?
                $
                """,
                uri,
                re.VERBOSE,
            )
        ):
            raise ValueError(f"Invalid uri. Should be {cls.URI_SCHEME}")

        uri_elems = match.groupdict()
        return cls(
            scheme=uri_elems["scheme"] or "",
            org=uri_elems["org"] or "",
            repo=uri_elems["image"] or "",
            tag=uri_elems["tag"] or "",
        )

    def __str__(self):
        return self.uri

    @property
    def uri(self):
        return "".join([f"{self.scheme}://" if self.scheme else "", self.address])

    @property
    def address(self):
        return "".join(
            [
                self.org + "/" if self.org else "",
                self.repo,
                ":" + self.tag if self.tag else "",
            ]
        )

    @property
    def image(self):
        return f"{self.org}/{self.repo}"


@attrs.frozen
class Container:
    uri: URI
    friendly_uri: Optional[URI] = None
    docker_data: Optional["DockerData"] = None

    @classmethod
    def from_uri(
        cls,
        uri: str,
        lookup_digest: bool = False,
        default: URI = URI(scheme="docker", repo="", org="library", tag=""),
    ):

        given = URI.parse(uri)
        if not given.tag:
            raise ValueError(f"Invalid uri. Must provide a tag. ({given.URI_SCHEME})")
        actual = attrs.evolve(
            default, **dict(filter(op.itemgetter(1), attrs.asdict(given).items()))
        )
        if lookup_digest and actual.scheme == "docker":
            data = DockerData.from_uri(actual)
        else:
            data = None
        return cls(uri=actual, friendly_uri=given, docker_data=data)

    @classmethod
    def from_uri_path(cls, path: Union[Path, str]):
        elems = Path(path).with_suffix("").parts
        if len(elems) > 4 or len(elems) < 3:
            raise ValueError(
                f"Incorrect number of parts in cache_path {path}. Expected 3 or 4"
            )
        if len(elems) == 4:
            tag = elems[3]
        else:
            tag = ""

        uri = URI(
            scheme=elems[0],
            org=elems[1],
            repo=elems[2],
            tag=tag or "",
        )
        friendly_uri = attrs.evolve(uri, org="") if uri.org == "library" else None
        return cls(uri=uri, friendly_uri=friendly_uri)

    @property
    def cache_path(self) -> Optional[str]:
        if self.docker_data and self.docker_data.trimmed_digest:
            return self.docker_data.trimmed_digest + ".sif"
        return None

    @property
    def uri_path(self):
        image_name = Path(self.uri.scheme, self.uri.org, self.uri.repo, self.uri.tag)
        return image_name.parent / (image_name.name + ".sif")

    @property
    def snakemake_cache_path(self):
        uri = self.friendly_uri or self.uri
        return Path(get_hash(uri.uri) + ".simg")

    def is_same_container(self, other: "Container"):
        return (
            other.uri.scheme == self.uri.scheme
            and other.uri.org == self.uri.org
            and other.uri.repo == self.uri.repo
        )

    def __str__(self):
        return str(self.friendly_uri or self.uri)


class ManifestError(CommandError):
    pass


@attrs.frozen
class DockerData:
    digest: str
    size: int

    @staticmethod
    def _get_target_arch():
        arch = platform.machine()
        if arch == "x86_64":
            return "amd64"
        elif arch.startswith("arm"):
            return "arm"
        elif arch.startswith("aarch64"):
            return "arm64"
        else:
            return None

    @staticmethod
    def _get_container_size(layers: list[dict[str, Any]]):
        return ft.reduce(op.add, map(op.itemgetter("size"), layers))

    @classmethod
    def from_uri(
        cls, uri: URI, digest: Optional[str] = None, token: Optional[str] = None
    ) -> Optional["DockerData"]:
        if token is None:
            token = requests.get(
                f"{AUTHBASE}/token",
                params=dict(
                    service=AUTHSERVICE,
                    scope=f"repository:{uri.image}:pull",
                ),
            ).json()["token"]

        digest = digest or uri.tag
        manifest_json = requests.get(
            f"{REGISTRYBASE}/v2/{uri.image}/manifests/{digest}",
            headers=dict(
                Authorization=f"Bearer {token}",
                Accept=(
                    "application/vnd.docker.distribution.manifest.v2+json, "
                    "application/vnd.docker.distribution.manifest.list.v2+json, "
                    "application/vnd.docker.distribution.manifest.v1+json"
                ),
            ),
        ).json()
        if "errors" in manifest_json:
            raise ManifestError(
                f"Unable to find '{uri}'. It may be a private repository, or you may "
                "have mispelled it."
            )

        schema_version = manifest_json["schemaVersion"]
        if schema_version == 2:
            media_type = manifest_json["mediaType"]
            if media_type == "application/vnd.docker.distribution.manifest.v2+json":
                return cls(
                    manifest_json["config"]["digest"],
                    size=cls._get_container_size(manifest_json["layers"]),
                )
            elif (
                media_type
                == "application/vnd.docker.distribution.manifest.list.v2+json"
            ):
                for manifest in manifest_json["manifests"]:
                    if manifest["platform"]["architecture"] == cls._get_target_arch():
                        return cls.from_uri(uri, digest=manifest["digest"], token=token)
        #     else:
        #         # fallback
        #         pass
        # elif schema_version == 1:
        #     # fallback
        #     pass
        # else:
        #     # fallback
        #     pass
        return None

    @property
    def trimmed_digest(self):
        if not (match := re.match(r".*\:(.*)", self.digest)):
            return None
        return match.group(1)

    @property
    def size_mb(self):
        return int(self.size / 1_000_000)


class SingularityDirError(CommandError):
    pass


class SingularityDir(type(Path())):
    def __new__(cls):
        pipdir = Config().get("pipdir")
        if pipdir is None:
            raise SingularityDirError(
                "pipdir not set. Please set pipdir using `kslurm config pipdir "
                "<directory>`, typically to a project-space or permanent storage "
                "directory"
            )
        pipdir = Path(pipdir)
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

    def has_raw_uri_file(self, container: Container):
        path = self.uris / container.uri_path
        return path.exists() and not path.is_symlink()

    def update_uri_link(self, container: Container):
        if container.cache_path:
            if (cache_path := self.images / container.cache_path).exists():
                uri_path = self.uris / container.uri_path
                if uri_path.exists():
                    if not uri_path.is_symlink():
                        os.remove(uri_path)
                    elif Path(cache_path).samefile(os.readlink(uri_path)):
                        return False
                    else:
                        os.unlink(uri_path)
                uri_path.parent.mkdir(exist_ok=True, parents=True)
                uri_path.symlink_to(cache_path)
                return True
            raise ValueError()
        return False

    def find(self, uri_or_alias: str):
        try:
            validators.fs_name(uri_or_alias)
        except ValidationError:
            container = None
        else:
            # Is it in the alias directory
            if (self.aliases / uri_or_alias).exists():
                container = ContainerAlias(uri_or_alias, self).image
            else:
                container = None

        if container is None:
            # Does it look like a uri
            try:
                container = Container.from_uri(uri_or_alias)
            except ValueError:
                raise SingularityDirError(
                    f"Invalid identifier '{uri_or_alias}'. Must be either an alias for "
                    "a container, or a valid container uri: "
                    f"'{URI.URI_SCHEME}'"
                )

        if (self.uris / container.uri_path).exists():
            return container
        return None

    def find_formatter(self, uri_or_alias: str):
        """Formatter version of find for use in argparser"""
        try:
            container = self.find(uri_or_alias)
        except SingularityDirError as err:
            raise ValidationError(err.msg)
        if container is None:
            raise ValidationError(f"No image with identifier '{uri_or_alias}' found")
        return container

    def iter_images(self):
        for dirpath, _, filenames in os.walk(self.uris):
            for filename in filenames:
                yield Path(dirpath, filename)


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
                Path(os.readlink(self.path)).relative_to(self.singularity_dir.uris)
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
        if self.path.is_symlink():
            if app == self.image:
                print(f"Alias '{self.alias}' already set to '{app}'")
                return
            print(f"Updating alias '{self.alias}' from {self.image} to {app}")
            self.path.unlink()
        else:
            print(f"Aliasing {app} as {self.alias}")
        self.path.symlink_to(self.singularity_dir.uris / app.uri_path)
        self._image = None


if __name__ == "__main__":
    container = Container.from_uri(
        "docker://akhanf/hippunfold:latest", lookup_digest=True
    )
    pass
