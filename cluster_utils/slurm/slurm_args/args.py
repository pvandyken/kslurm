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
        value = formatters.time("03:00"))

    gpu: FlagArg = FlagArg(
        match = ["gpu"])

    cpu: ShapeArg[int] = ShapeArg[int](
        match = lambda arg: bool(re.match(r'^[0-9]+$', arg)),
        value = 1,
        format = int)

    mem: ShapeArg[int] = ShapeArg[int](
        match = lambda arg: bool(re.match(r'^[0-9]+[MG]B?$', arg)),
        format = formatters.mem,
        value = formatters.mem("4G"))

    jupyter: FlagArg = FlagArg(
        match=["jupyter"]
    )

    directory: ShapeArg[Path] = ShapeArg[Path](
        match = lambda arg: Path(arg).exists() and Path(arg).is_dir(),
        format = Path,
        value = Path()) 

    test: FlagArg = FlagArg(
        match=["-t", "--test"]
    )

    job_template: KeywordArg[str] = KeywordArg[str](
        match=lambda arg : arg == '-j' or arg == '--job-template',
        validate=validators.job_template,
        num=1)

    list_job_templates: FlagArg= FlagArg(
        match=["-J", "--list", "-l"]
    )
    
    account: KeywordArg[str] = KeywordArg[str](
        match=lambda arg: arg == '-a' or arg == '--account',
        num=1,
        values=['def-lpalaniy']
    )
    
    tail: TailArg = TailArg()



