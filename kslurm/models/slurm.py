from __future__ import absolute_import

import re
from pathlib import Path

import attr

import kslurm.models.formatters as formatters
import kslurm.models.validators as validators
from kslurm.args import FlagArg, KeywordArg, ShapeArg, TailArg


@attr.s(auto_attribs=True)
class SlurmModel:
    time: ShapeArg[int] = ShapeArg[int](
        match=lambda arg: bool(re.match(r"^([0-9]{1,2}-)?[0-9]{1,2}:[0-9]{2}$", arg)),
        format=formatters.time,
        value="03:00",
        name="Time",
        syntax="[d-]dd:dd",
        help="Amount of time requested. Written as [days-]hr:min.",
        examples=["3:00 (3hr)", "1-00:00 (1 day)"],
    )

    gpu: FlagArg = FlagArg(match=["gpu"], help="Request a gpu instance")

    cpu: ShapeArg[int] = ShapeArg[int](
        match=lambda arg: bool(re.match(r"^[0-9]+$", arg)),
        value="1",
        format=int,
        name="Number of CPUs",
        syntax="d",
        help="Number of CPUs to request. Maximum of 32 on Graham Nodes.",
        examples=["1 (1 cpu)", "16 (16 cpus)"],
    )

    mem: ShapeArg[int] = ShapeArg[int](
        match=lambda arg: bool(re.match(r"^[0-9]+[MG]B?$", arg)),
        format=formatters.mem,
        value="4G",
        name="Memory",
        syntax="d(M|G)[B]",
        examples=["3000MB (3 GB)", "16G (16GB)"],
        help="Amount of memory to request",
    )

    x11: FlagArg = FlagArg(
        match=["x11", "--x11"],
        help="Request X-forwarding for GUI applications. Must also request "
        "X-forwarding on your SSH connection.",
    )

    directory: ShapeArg[Path] = ShapeArg[Path](
        match=lambda arg: Path(arg).exists() and Path(arg).is_dir(),
        format=Path,
        value=".",
        name="Directory",
        syntax="/absolute/path | ./relative/path",
        help="Change working directory before submitting the command. All other "
        "relative paths will be evaluated relative to the new directory.",
    )

    test: FlagArg = FlagArg(
        match=["-t", "--test"],
        help="Test mode. Will echo SLURM settings and the command without submitting "
        "anything.",
    )

    job_template: KeywordArg[str] = KeywordArg[str](
        match=["-j", "--job-template"],
        validate=validators.job_template,
        num=1,
        values_name="template",
        help="Set CPU, memory, and time from a template. "
        "Run with -J to see list of templates. Any "
        "template item can be overridden by supplying "
        "the appropriate arg.",
    )

    list_job_templates: FlagArg = FlagArg(
        match=["-J", "--list", "-l"], help="List all available templates."
    )

    account: KeywordArg[str] = KeywordArg[str](
        match=["-a", "--account"],
        num=1,
        values=["ctb-akhanf"],
        help="Compute account to submit the job under.",
        values_name="name",
    )

    help: FlagArg = FlagArg(match=["-h", "--help"], help="Print this help message")

    tail: TailArg = TailArg("Command")
