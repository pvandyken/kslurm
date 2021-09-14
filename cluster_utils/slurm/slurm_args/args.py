import re
from pathlib import Path
import attr
from cluster_utils.args import ShapeArg, KeywordArg, FlagArg, TailArg
from . import formatters
from . import validators

@attr.s(auto_attribs=True)
class ArgList:
    time: ShapeArg[int] = ShapeArg[int](
        match = lambda arg: bool(re.match(r'^([0-9]{1,2}-)?[0-9]{1,2}:[0-9]{2}$', arg)),
        format = formatters.time,
        value = formatters.time("03:00"),
        name="Time",
        syntax="[d-]dd:dd",
        help="Amount of time requested. Written as [days-]hr:min.",
        examples=[
            "3:00 (3hr)",
            "1-00:00 (1 day)"
        ])

    gpu: FlagArg = FlagArg(
        match = ["gpu"],
        help="Request a gpu instance")

    cpu: ShapeArg[int] = ShapeArg[int](
        match = lambda arg: bool(re.match(r'^[0-9]+$', arg)),
        value = 1,
        format = int,
        name = "Number of CPUs",
        syntax="d",
        help="Number of CPUs to request. Maximum of 32 on Graham Nodes.",
        examples=[
            "1 (1 cpu)",
            "16 (16 cpus)"
        ])

    mem: ShapeArg[int] = ShapeArg[int](
        match = lambda arg: bool(re.match(r'^[0-9]+[MG]B?$', arg)),
        format = formatters.mem,
        value = formatters.mem("4G"),
        name = "Memory",
        syntax="d(M|G)[B]",
        examples=[
            "3000MB (3 GB)",
            "16G (16GB)"
        ])

    x11: FlagArg = FlagArg(
        match=["x11", "--x11"],
        help="Request X-forwarding for GUI applications. Must also request X-forwarding on your SSH connection."
    )

    directory: ShapeArg[Path] = ShapeArg[Path](
        match = lambda arg: Path(arg).exists() and Path(arg).is_dir(),
        format = Path,
        value = Path(),
        name = "Directory",
        syntax="/absolute/path | relative/path",
        help="Change working directory before submitting the command. All other "
             "relative paths will be evaluated relative to the new directory.") 

    test: FlagArg = FlagArg(
        match=["-t", "--test"],
        help="Test mode. Will echo SLURM settings and the command without submitting anything."
    )

    job_template: KeywordArg[str] = KeywordArg[str](
        match=lambda arg : arg == '-j' or arg == '--job-template',
        validate=validators.job_template,
        num=1,
        help="Set CPU, memory, and time from a template. "
             "Run with -J to see list of templates. Any "
             "template item can be overridden by supplying "
             "the appropriate arg.")

    list_job_templates: FlagArg= FlagArg(
        match=["-J", "--list", "-l"],
        help="List all available templates."
    )
    
    account: KeywordArg[str] = KeywordArg[str](
        match=lambda arg: arg == '-a' or arg == '--account',
        num=1,
        values=['def-lpalaniy'],
        help="Compute account to submit the job under."
    )
    
    tail: TailArg = TailArg()



