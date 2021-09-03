from typing import List
import re
from pathlib import Path
import cluster_utils.args.arg_constructors as constructors
import cluster_utils.args.formatters as formatters
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

shape_arg = constructors.ShapeArgConstructor
keyword_arg = constructors.KeywordArgConstructor


command_arg = constructors.ShapeArgConstructor(COMMAND)

arg_list: List[constructors.ArgConstructor] = [
    shape_arg(TIME,
             lambda arg: bool(re.match(r'^([0-9]{1,2}-)?[0-9]{1,2}:[0-9]{2}$', arg)),
             formatters.time),
    shape_arg(GPU, 
             lambda arg: arg == "gpu"),
    shape_arg(CPU, 
             lambda arg: bool(re.match(r'^[0-9]+$', arg))),
    shape_arg(MEM, 
             lambda arg: bool(re.match(r'^[0-9]+[MG]B?$', arg)),
             formatters.mem),
    shape_arg(JUPYTER, 
             lambda arg: arg == "jupyter"),
    shape_arg(DIRECTORY, 
             lambda arg: Path(arg).exists() and Path(arg).is_dir()),
    shape_arg(TEST, 
             lambda arg: arg == "-t" or arg == "--test"),
    keyword_arg(JOB_TEMPLATE, 
              lambda arg : arg == '-j' or arg == '--job-template',
              1)
]