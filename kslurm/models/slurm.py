from __future__ import absolute_import

from pathlib import Path

import attr

import kslurm.models.formatters as formatters
import kslurm.models.validators as validators
from kslurm.args import flag, keyword, path, shape


@attr.s(auto_attribs=True)
class SlurmModel:
    """
    Attributes:
        time (int):
            Amount of time requested. Written as [days-]hr:min
            @help.syntax [d-]dd:dd
            @name Time

        gpu:
            Request a gpu instance

        cpu:
            Number of CPUs to request. Maximum of 32 on Graham Nodes
            @help.syntax d
            @name Number of CPUs

        mem:
            Amount of memory to request
            @help.syntax d(M|G)[B]
            @name Memory

        x11:
            Request X-forwarding for GUI applications. Must also request X-forwarding on
            your SSH connection.

        directory:
            Change working directory before submitting the command. All other relative
            paths will be evaluated relative to the new directory.
            @name Directory

        test:
            Test mode. Will echo SLURM settings and the command without submitting
            anything.

        job_template:
            Set CPU, memory, and time from a template. Run with -J to see list of
            templates. Any template item can be overridden by supplying the appropriate
            arg.

        list_job_templates:
            List all available templates.

        account:
            Compute account to submit the job under.

        venv:
            kpy venv to load
    """

    time: int = shape(
        match=r"^([0-9]{1,2}-)?[0-9]{1,2}:[0-9]{2}$",
        format=formatters.time,
        default=180,
        examples=["3:00 (3hr)", "1-00:00 (1 day)"],
    )

    gpu: bool = flag(match=["gpu"])

    cpu: int = shape(
        match=r"^[0-9]+$",
        default=1,
        examples=["1 (1 cpu)", "16 (16 cpus)"],
    )

    mem: int = shape(
        match=r"^[0-9]+[KMGkmg][Ii]?[Bb]?$",
        format=formatters.mem,
        default=4000,
        examples=["3000MB (3 GB)", "16G (16GB)"],
    )

    x11: bool = flag(match=["x11", "--x11"])

    directory: Path = path(
        default=Path(),
        dir_only=True,
    )

    test: bool = flag(match=["-t", "--test"])

    job_template: str = keyword(
        match=["-j", "--job-template"], format=validators.job_template
    )

    list_job_templates: bool = flag(match=["-J", "--list", "-l"])

    account: str = keyword(match=["-a", "--account"])

    venv: str = keyword(["--venv"], default="")
