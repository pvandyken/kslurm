from __future__ import absolute_import

import attr

import kslurm.appconfig as appconfig
from kslurm.args import positional
from kslurm.args.command import command


@attr.frozen
class ConfigModel:
    entry: str = positional(help="Configuration value to update")
    value: str = positional(
        default="",
        help="Updated value for config entry. If not provided, the current config "
        "value is printed",
    )


@command
def config(args: ConfigModel):
    """Read and write from the kslurm config"""
    if not args.value:
        value = appconfig.get_config(args.entry)
        if value is None:
            print("")
        else:
            print(value)

    else:
        appconfig.set_config(args.entry, args.value)
