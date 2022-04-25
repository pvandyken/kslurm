from __future__ import absolute_import

import subprocess
from typing import Union

from colorama import Fore

import kslurm.text as txt
from kslurm.args.command import command
from kslurm.exceptions import TemplateError
from kslurm.models import SlurmModel
from kslurm.slurm import SlurmCommand


@command
def kbatch(args: Union[SlurmModel, TemplateError]):
    """Submit a job using sbatch

    Supports scripts (e.g. ./script.sh) or direct commands (e.g. cp dir/file.txt dir2)

    When your command contains bash interpreted elements such as $VARIABLES and
    $(subshells), these will be immediately expanded. Normally, this behaviour
    is fine, but sometimes they should only be interpretted on the allocated cluster.
    For instance, $SLURM_TMPDIR will evaluate to "" unless it is interpretted later.
    To force this behaviour, wrap the $VARIABLE or $(subshell) in quotes:
        '$SLURM_TMPDIR'
        '$(hostname)'
    """

    slurm = SlurmCommand(args)
    command = slurm.command if slurm.command else f"{Fore.RED}Must provide a command"

    print(txt.KBATCH_MSG.format(slurm_args=slurm.slurm_args, command=command))
    if slurm.command:
        proc = subprocess.run(
            slurm.batch, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
        )

        out = proc.stdout.decode()

        if proc.returncode != 0:
            print(Fore.WHITE + out)
        if slurm.test:
            # output will be the issued command, so we print it
            print(Fore.WHITE + out)
        else:
            # We subtract the last character of the output
            # to remove the final "\n" character and get the
            # job_id
            slurmid = out[:-1]

            print(
                f"""Scheduled job {slurmid}.
    To cancel, run:
        scancel {slurmid}
        """
            )


if __name__ == "__main__":
    kbatch()
