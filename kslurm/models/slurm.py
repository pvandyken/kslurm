from __future__ import absolute_import

import re
from pathlib import Path

import attr

import kslurm.models.formatters as formatters
import kslurm.models.validators as validators
from kslurm.args import flag, keyword, shape


@attr.s(auto_attribs=True)
class SlurmModel:
    time: int = shape(
        match=lambda arg: bool(re.match(r"^([0-9]{1,2}-)?[0-9]{1,2}:[0-9]{2}$", arg)),
        format=formatters.time,
        default="03:00",
        name="Time",
        syntax="[d-]dd:dd",
        help="Amount of time requested. Written as [days-]hr:min.",
        examples=["3:00 (3hr)", "1-00:00 (1 day)"],
    )

    gpu: bool = flag(match=["gpu"], help="Request a gpu instance")

    cpu: int = shape(
        match=lambda arg: bool(re.match(r"^[0-9]+$", arg)),
        default="1",
        name="Number of CPUs",
        syntax="d",
        help="Number of CPUs to request. Maximum of 32 on Graham Nodes.",
        examples=["1 (1 cpu)", "16 (16 cpus)"],
    )

    mem: int = shape(
        match=lambda arg: bool(re.match(r"^[0-9]+[MG]B?$", arg)),
        format=formatters.mem,
        default="4G",
        name="Memory",
        syntax="d(M|G)[B]",
        examples=["3000MB (3 GB)", "16G (16GB)"],
        help="Amount of memory to request",
    )

    x11: bool = flag(
        match=["x11", "--x11"],
        help="Request X-forwarding for GUI applications. Must also request "
        "X-forwarding on your SSH connection.",
    )

    directory: Path = shape(
        match=lambda arg: Path(arg).exists() and Path(arg).is_dir(),
        default=".",
        name="Directory",
        syntax="/absolute/path | ./relative/path",
        help="Change working directory before submitting the command. All other "
        "relative paths will be evaluated relative to the new directory.",
    )

    test: bool = flag(
        match=["-t", "--test"],
        help="Test mode. Will echo SLURM settings and the command without submitting "
        "anything.",
    )

    job_template: list[str] = keyword(
        match=["-j", "--job-template"],
        validate=validators.job_template,
        num=1,
        help="Set CPU, memory, and time from a template. "
        "Run with -J to see list of templates. Any "
        "template item can be overridden by supplying "
        "the appropriate arg.",
    )

    list_job_templates: bool = flag(
        match=["-J", "--list", "-l"], help="List all available templates."
    )

    account: list[str] = keyword(
        match=["-a", "--account"],
        num=1,
        help="Compute account to submit the job under.",
    )
