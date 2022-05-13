from __future__ import absolute_import

import platform
import re
from pathlib import Path
from typing import Optional, Union

import attrs
import requests

from kslurm.args.command import CommandError
from kslurm.utils import get_hash

REGISTRYBASE = "https://registry-1.docker.io"
AUTHBASE = "https://auth.docker.io"
AUTHSERVICE = "registry.docker.io"


@attrs.frozen
class Container:
    scheme: str
    org: str
    repo: str
    tag: str
    digest: str = ""

    URI_SCHEME = "<scheme>://[<org>/]<image>[:<tag>][@sha256:<digest>]"

    @classmethod
    def from_uri(cls, uri: str, lookup_digest: bool = False):
        if not (
            match := re.match(
                r"""
                ^(?P<scheme>[^:\/]+)
                \:\/\/
                (?:(?P<org>[^\/]*)\/)?
                (?P<image>[^:]+)
                (?::(?P<tag>[^\@]+))?
                (?:\@(?P<digest>sha256\:.+))?
                $
                """,
                uri,
                re.VERBOSE,
            )
        ):
            raise ValueError(f"Invalid uri. Should be {cls.URI_SCHEME}")

        uri_elems = match.groupdict()

        if not uri_elems["tag"] and not uri_elems["digest"]:
            raise ValueError(
                f"Invalid uri. Must provide a tag and/or digest. ({cls.URI_SCHEME})"
            )
        container: Container = cls(
            scheme=uri_elems["scheme"] or "",
            org=uri_elems["org"] or "library",
            repo=uri_elems["image"] or "",
            tag=uri_elems["tag"] or "",
            digest=uri_elems["digest"] or "",
        )
        if lookup_digest and not uri_elems["digest"]:
            return attrs.evolve(container, digest=get_digest(container) or "")
        return container

    @classmethod
    def from_uri_path(cls, path: Union[Path, str]):
        elems = Path(path).with_suffix("").parts
        if len(elems) > 4 or len(elems) < 3:
            raise ValueError(
                f"Incorrect number of parts in cache_path {path}. Expected 3 or 4"
            )
        return cls(
            scheme=elems[0],
            org=elems[1],
            repo=elems[2],
            tag=elems[3] if len(elems) == 4 else "",
        )

    @property
    def uri(self):
        return f"{self.scheme}://{self.address}"

    @property
    def address(self):
        return (
            f"{self.org + '/' if self.org and self.org != 'library' else ''}{self.repo}"
            f"{':' + self.tag if self.tag else ''}"
        )

    @property
    def image(self):
        return f"{self.org}/{self.repo}"

    @property
    def cache_path(self) -> Optional[str]:
        if not (match := re.match(r".*\:(.*)", self.digest)):
            return None
        return match.group(1) + ".sif"

    @property
    def uri_path(self):
        image_name = Path(self.scheme, self.org or "libary", self.repo, self.tag)
        return image_name.parent / (image_name.name + ".sif")

    @property
    def snakemake_cache_path(self):
        return Path(get_hash(self.uri) + ".simg")

    def is_same_container(self, other: "Container"):
        return (
            other.scheme == self.scheme
            and other.org == self.org
            and other.repo == self.repo
        )

    def __str__(self):
        return self.address


class ManifestError(CommandError):
    pass


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


def get_digest(container: Container, token: Optional[str] = None) -> Optional[str]:
    if token is None:
        token = requests.get(
            f"{AUTHBASE}/token",
            params=dict(
                service=AUTHSERVICE,
                scope=f"repository:{container.image}:pull",
            ),
        ).json()["token"]

    digest = container.digest or container.tag
    manifest_json = requests.get(
        f"{REGISTRYBASE}/v2/{container.image}/manifests/{digest}",
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
            f"Unable to find '{container}'. It may be a private repository, or you may "
            "have mispelled it."
        )

    schema_version = manifest_json["schemaVersion"]
    if schema_version == 2:
        media_type = manifest_json["mediaType"]
        if media_type == "application/vnd.docker.distribution.manifest.v2+json":
            return manifest_json["config"]["digest"]
        elif media_type == "application/vnd.docker.distribution.manifest.list.v2+json":
            for manifest in manifest_json["manifests"]:
                if manifest["platform"]["architecture"] == _get_target_arch():
                    return get_digest(
                        attrs.evolve(container, digest=manifest["digest"]), token=token
                    )
    #     else:
    #         # fallback
    #         pass
    # elif schema_version == 1:
    #     # fallback
    #     pass
    # else:
    #     # fallback
    #     pass
    print(manifest_json)


if __name__ == "__main__":
    container = Container(scheme="docker", org="library", repo="ubuntu", tag="latest")
    print(get_digest(container))
