from ..job_templates import templates
from cluster_utils.exceptions import TemplateError


def job_template(arg: str) -> str:
    if arg in templates:
        return arg
    raise TemplateError(f"{arg} is not a valid job-template")