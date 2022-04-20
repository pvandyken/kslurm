from __future__ import absolute_import

from typing import List

import kslurm.appconfig as appconfig
from kslurm import print_help
from kslurm.args.parser import parse_args
from kslurm.models.config import ConfigModel


def config(args: List[str]):
    parsed = parse_args(args, ConfigModel())
    if parsed.help.value:
        print_help("kslurm config", ConfigModel())

    if not parsed.value.value:
        print(appconfig.get_config(parsed.entry.value))
    else:
        appconfig.set_config(parsed.entry.value, parsed.value.value)
