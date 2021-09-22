from __future__ import absolute_import

import attr

from kslurm.args import ChoiceArg, TailArg


@attr.s(auto_attribs=True)
class KslurmModel:
    command: ChoiceArg[str] = ChoiceArg[str](
        match=["kbatch", "krun", "kjupyter", "update"],
        name="Command",
        help="Run any of the commands with -h to get more information",
    )

    tail: TailArg = TailArg("Args")
