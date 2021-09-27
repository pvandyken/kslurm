__submodules__ = ["args", "installer", "models", "slurm", "submission", "kslurm"]

__ignore__ = ["main"]

# <AUTOGEN_INIT>
from kslurm.args import (
    Arg,
    ChoiceArg,
    FlagArg,
    KeywordArg,
    PositionalArg,
    ShapeArg,
    TailArg,
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
from kslurm.kslurm import (
    ENTRYPOINTS,
    HOME_DIR,
    NAME,
    kslurm,
)

__all__ = [
    "Arg",
    "ChoiceArg",
    "ENTRYPOINTS",
    "FlagArg",
    "HOME_DIR",
    "KeywordArg",
    "KslurmModel",
    "METADATA_URL",
    "NAME",
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
    "install",
    "job_template",
    "kbatch",
    "kjupyter",
    "krun",
    "kslurm",
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
