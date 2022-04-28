from __future__ import absolute_import

from kslurm.args.arg import Arg
from kslurm.args.arg_types import positional


def positional_models(num: int) -> list[Arg[str, None]]:
    return [positional(f"pos{num}") for _ in range(num)]
