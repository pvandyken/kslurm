from __future__ import absolute_import, annotations

import re
from typing import Union, cast

import semver


class FlexVersion(semver.VersionInfo):
    raw_value: str
    _REGEX = re.compile(
        r"""
            ^
            (?P<major>0|[1-9]\d*)
            (?:\.
                (?P<minor>0|[1-9]\d*)
            )?
            (?:\.
                (?P<patch>0|[1-9]\d*)
            )?
            [._-]?
            (?:(?P<prerelease>
                (?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)
                (?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*
            ))?
            (?:\+(?P<build>
                [0-9a-zA-Z-]+
                (?:\.[0-9a-zA-Z-]+)*
            ))?
            $
        """,
        re.VERBOSE,
    )

    @classmethod
    def parse(cls, version: Union[str, bytes]):
        parsed = cast("FlexVersion", super().parse(version))
        parsed.raw_value = str(version)
        return parsed
