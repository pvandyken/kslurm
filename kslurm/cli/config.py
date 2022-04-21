from __future__ import absolute_import

import attr

import kslurm.appconfig as appconfig
from kslurm.args.arg_types import FlagArg, PositionalArg
from kslurm.args.command import command


@attr.frozen
class ConfigModel:
    entry: PositionalArg[str] = PositionalArg(help="Configuration value to update")
    value: PositionalArg[str] = PositionalArg(
        value="",
        help="Updated value for config entry. If not provided, the current config "
        "value is printed",
    )
    help: FlagArg = FlagArg(match=["-h", "--help"], help="Show this help message")


@command
def config(args: ConfigModel):
    if not args.value.value:
        value = appconfig.get_config(args.entry.value)
        if value is None:
            print("")
        else:
            print(value)

    else:
        appconfig.set_config(args.entry.value, args.value.value)
