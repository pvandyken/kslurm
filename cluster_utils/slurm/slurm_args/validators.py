from ..job_templates import templates


def job_template(arg: str) -> bool:
    if arg in templates:
        return True
    else:
        return False
        #raise Exception(f"{arg} is not a valid job-template")