__submodules__ = ["args", "installer", "models", "slurm", "submission"]

__ignore__ = ["main"]

# <AUTOGEN_INIT>
from kslurm.args import (
    Arg,
    ArgSorter,
    ChoiceArg,
    FlagArg,
    KeywordArg,
    PositionalArg,
    ShapeArg,
    TailArg,
    group_by_type,
    parse_args,
    print_help,
)
from kslurm.installer import (
    METADATA_URL,
    install,
    run_installation,
)
from kslurm.models import (
    KslurmModel,
    SlurmModel,
    TemplateArgs,
    Templates,
    UpdateModel,
    VERSION_REGEX,
    job_template,
    list_templates,
    mem,
    set_template,
    templates,
    time,
)
from kslurm.slurm import (
    SlurmCommand,
    div_remainder,
    slurm_time_format,
)
from kslurm.submission import (
    kbatch,
    kjupyter,
    krun,
)

__all__ = [
    "Arg",
    "ArgSorter",
    "ChoiceArg",
    "FlagArg",
    "KeywordArg",
    "KslurmModel",
    "METADATA_URL",
    "PositionalArg",
    "ShapeArg",
    "SlurmCommand",
    "SlurmModel",
    "TailArg",
    "TemplateArgs",
    "Templates",
    "UpdateModel",
    "VERSION_REGEX",
    "div_remainder",
    "group_by_type",
    "install",
    "job_template",
    "kbatch",
    "kjupyter",
    "krun",
    "list_templates",
    "mem",
    "parse_args",
    "print_help",
    "run_installation",
    "set_template",
    "slurm_time_format",
    "templates",
    "time",
]

# </AUTOGEN_INIT>
