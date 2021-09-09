from cluster_utils.args.arg_types import TailArg
import re
from pathlib import Path
import attr
from cluster_utils.args import ShapeArg, KeywordArg
import cluster_utils.slurm.slurm_args.formatters as formatters

@attr.s(auto_attribs=True)
class ArgList:
    time: ShapeArg[int] = ShapeArg[int](
        match = lambda arg: bool(re.match(r'^([0-9]{1,2}-)?[0-9]{1,2}:[0-9]{2}$', arg)),
        format = formatters.time,
        value = formatters.time("03:00"))

    gpu: ShapeArg[bool] = ShapeArg[bool](
        match = lambda arg: arg == "gpu",
        format = bool,
        value = False)

    cpu: ShapeArg[int] = ShapeArg[int](
        match = lambda arg: bool(re.match(r'^[0-9]+$', arg)),
        value = 1,
        format = int)

    mem: ShapeArg[int] = ShapeArg[int](
        match = lambda arg: bool(re.match(r'^[0-9]+[MG]B?$', arg)),
        format = formatters.mem,
        value = formatters.mem("4G"))

    jupyter: ShapeArg[bool] = ShapeArg[bool](
        match = lambda arg: arg == "jupyter",
        format = bool,
        value = False)

    directory: ShapeArg[Path] = ShapeArg[Path](
        match = lambda arg: Path(arg).exists() and Path(arg).is_dir(),
        format = Path,
        value = Path()) 

    test: ShapeArg[bool] = ShapeArg[bool](
        match = lambda arg: arg == "-t" or arg == "--test",
        format = bool,
        value = False)

    job_template: KeywordArg[str] = KeywordArg[str](
        match=lambda arg : arg == '-j' or arg == '--job-template',
        num=1)
    
    account: KeywordArg[str] = KeywordArg[str](
        match=lambda arg: arg == '-a' or arg == '--account',
        num=1,
        values=['def-lpalaniy']
    )
    
    tail: TailArg = TailArg()



