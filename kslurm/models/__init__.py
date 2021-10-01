__submodules__ = [
    "formatters",
    "kslurm",
    "slurm",
    "update",
    "validators",
    "job_templates",
]

# <AUTOGEN_INIT>
from kslurm.models.formatters import (
    mem,
    time,
)
from kslurm.models.kslurm import (
    KslurmModel,
)
from kslurm.models.slurm import (
    SlurmModel,
)
from kslurm.models.update import (
    UpdateModel,
    VERSION_REGEX,
)
from kslurm.models.validators import (
    job_template,
)
from kslurm.models.job_templates import (
    TemplateArgs,
    Templates,
    list_templates,
    set_template,
    templates,
)

__all__ = [
    "KslurmModel",
    "SlurmModel",
    "TemplateArgs",
    "Templates",
    "UpdateModel",
    "VERSION_REGEX",
    "job_template",
    "list_templates",
    "mem",
    "set_template",
    "templates",
    "time",
]

# </AUTOGEN_INIT>
