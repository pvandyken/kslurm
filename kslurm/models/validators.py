from kslurm.slurm.job_templates import templates
from kslurm.exceptions import TemplateError


def job_template(arg: str) -> str:
    if arg in templates():
        return arg
    raise TemplateError(f"{arg} is not a valid job-template")