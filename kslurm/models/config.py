from __future__ import absolute_import

import attr

from kslurm.args.arg_types import FlagArg, PositionalArg


@attr.frozen
class ConfigModel:
    entry: PositionalArg[str] = PositionalArg(help="Configuration value to update")
    value: PositionalArg[str] = PositionalArg(
        value="",
        help="Updated value for config entry. If not provided, the current config "
        "value is printed",
    )
    help: FlagArg = FlagArg(match=["-h", "--help"], help="Show this help message")
