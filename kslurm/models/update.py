from __future__ import absolute_import

import re

import attr

from kslurm.args import ShapeArg, TailArg

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
    version: ShapeArg[str] = ShapeArg[str](
        match=lambda arg: bool(re.match(VERSION_REGEX, arg)),
        value="",
        name="Version",
        syntax="d[.d][.d][.d][_tag]",
        examples=["0.1.0"],
        help="Optional: version to install",
    )

    tail: TailArg = TailArg()
