from __future__ import absolute_import

from kslurm.exceptions import TemplateError
from kslurm.models.job_templates import templates


def job_template(arg: str) -> str:
    if arg in templates():
        return arg
    raise TemplateError(f"{arg} is not a valid job-template")
