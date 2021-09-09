from cluster_utils.args.arg_types import TailArg
import re
from pathlib import Path
import attr
from cluster_utils.args import ShapeArg, KeywordArg
import cluster_utils.slurm.slurm_args.formatters as formatters

@attr.s(auto_attribs=True)
class ArgList:
    time: ShapeArg[int] = ShapeArg(
        match = lambda arg: bool(re.match(r'^([0-9]{1,2}-)?[0-9]{1,2}:[0-9]{2}$', arg)),
        format = formatters.time,
        value = "03:00")

    gpu: ShapeArg[bool] = ShapeArg(
        match = lambda arg: arg == "gpu",
        format = bool)

    cpu: ShapeArg[int] = ShapeArg(
        match = lambda arg: bool(re.match(r'^[0-9]+$', arg)),
        value = 1,
        format = int)

    mem: ShapeArg[str] = ShapeArg(
        match = lambda arg: bool(re.match(r'^[0-9]+[MG]B?$', arg)),
        format = formatters.mem,
        value = "4G")

    jupyter: ShapeArg[bool] = ShapeArg(
        match = lambda arg: arg == "jupyter",
        format = bool)

    directory: ShapeArg[Path] = ShapeArg(
        match = lambda arg: Path(arg).exists() and Path(arg).is_dir(),
        format = Path) # type: ignore

    test: ShapeArg[bool] = ShapeArg(
        match = lambda arg: arg == "-t" or arg == "--test",
        format = bool)

    job_template: KeywordArg[str] = KeywordArg(
        match=lambda arg : arg == '-j' or arg == '--job-template',
        num=1)
    
    account: KeywordArg[str] = KeywordArg(
        match=lambda arg: arg == '-a' or arg == '--account',
        num=1,
        values=['def-lpalaniy']
    )
    
    tail: TailArg = TailArg()



