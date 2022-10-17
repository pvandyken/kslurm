from __future__ import absolute_import, annotations

import re

from kslurm.exceptions import TemplateError, ValidationError
from kslurm.models.job_templates import templates


def job_template(arg: str) -> str:
    if arg in templates():
        return arg
    raise TemplateError(f"{arg} is not a valid job-template")


_FS_NAME_PATTERN = re.compile(r"^[\w\-\. ]+$")


def fs_name(name: str):
    if name and not re.match(_FS_NAME_PATTERN, name):
        raise ValidationError(f"Invalid characters found in {name}")
    return name
