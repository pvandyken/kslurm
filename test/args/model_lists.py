from __future__ import absolute_import

from kslurm.args.arg_types import PositionalArg


def positional_models(num: int):
    return [PositionalArg() for _ in range(num)]
