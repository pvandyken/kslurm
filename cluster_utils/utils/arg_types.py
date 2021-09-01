from typing import Callable, Dict
from pathlib import Path
import re


TIME = 'time'
GPU = 'gpu'
CPU = 'cpus'
MEM = 'mem'
JUPYTER = 'jupyter'
ACCOUNT = 'account'
COMMAND = 'command'
DIRECTORY = 'directory'
TEST = 'test'

data: Dict[str, Callable[[str], bool]] = {
    TIME: lambda arg: re.match(r'^([0-9]{1,2}-)?[0-9]{1,2}:[0-9]{2}$', arg),
    GPU: lambda arg: arg == "gpu",
    CPU: lambda arg: re.match(r'^[0-9]+$', arg),
    MEM: lambda arg: re.match(r'^[0-9]+[MG]B?$', arg),
    JUPYTER: lambda arg: arg == "jupyter",
    DIRECTORY: lambda arg: Path(arg).exists() and Path(arg).is_dir(),
    TEST: lambda arg: arg == "-t" or arg == "--test"
}