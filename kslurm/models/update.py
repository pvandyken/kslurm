from __future__ import absolute_import, annotations

import re

import attr

from kslurm.args import shape

# v(major_version).(minor_version).(patch_version).(sub_patch_version)
VERSION_REGEX = (
    r"v?(\d+)(?:\.(\d+))?(?:\.(\d+))?(?:\.(\d+))?"
    "("
    "[._-]?"
    r"(?:(stable|beta|b|rc|RC|alpha|a|patch|pl|p)((?:[.-]?\d+)*)?)?"
    "([.-]?dev)?"
    ")?"
    r"(?:\+[^\s]+)?"
)


@attr.s(auto_attribs=True)
class UpdateModel:
    version: str = shape(
        match=lambda arg: bool(re.match(VERSION_REGEX, arg)),
        default="",
        name="Version",
        syntax="d[.d][.d][.d][_tag]",
        examples=["0.1.0"],
        help="Optional: version to install",
    )
