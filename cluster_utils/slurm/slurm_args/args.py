from cluster_utils.args.arg_types import TailArg
import re
from pathlib import Path
import attr
from cluster_utils.args import ShapeArg, KeywordArg
import cluster_utils.slurm.slurm_args.formatters as formatters
TIME = 'time'
GPU = 'gpu'
CPU = 'cpus'
MEM = 'mem'
JUPYTER = 'jupyter'
ACCOUNT = 'account'
COMMAND = 'command'
DIRECTORY = 'directory'
TEST = 'test'
JOB_TEMPLATE = 'job template'

shape_arg = ShapeArg
keyword_arg = KeywordArg

@attr.s(auto_attribs=True)
class ArgList:
    time: ShapeArg = shape_arg(
             id = "time",
             match = lambda arg: bool(re.match(r'^([0-9]{1,2}-)?[0-9]{1,2}:[0-9]{2}$', arg)),
             format = formatters.time,
             value = "03:00")

    gpu: shape_arg = shape_arg(
             id = "gpu", 
             match = lambda arg: arg == "gpu")

    cpu: shape_arg = shape_arg(
             id = "cpu", 
             match = lambda arg: bool(re.match(r'^[0-9]+$', arg)),
             value = "1")

    mem: shape_arg = shape_arg(
             id = "mem", 
             match = lambda arg: bool(re.match(r'^[0-9]+[MG]B?$', arg)),
             format = formatters.mem,
             value = "4G")

    jupyter: shape_arg = shape_arg(
             id = "jupyter", 
             match = lambda arg: arg == "jupyter")

    directory: shape_arg = shape_arg(
             id = "directory", 
             match = lambda arg: Path(arg).exists() and Path(arg).is_dir())

    test: shape_arg = shape_arg(
             id = "test", 
             match = lambda arg: arg == "-t" or arg == "--test")

    job_template: keyword_arg = keyword_arg(
              id="job template", 
              match=lambda arg : arg == '-j' or arg == '--job-template',
              num=1)
    
    account: keyword_arg = keyword_arg(
        match=lambda arg: arg == '-a' or arg == '--account',
        num=1,
        values=['def-lpalaniy']
    )
    
    tail: TailArg = TailArg()



