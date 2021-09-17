from typing import List
import sys, subprocess
from colorama import Fore
from kslurm.slurm import SlurmCommand
from kslurm.models import SlurmModel
from kslurm.args import print_help
from .. import text as txt

def kbatch(script: str, args: List[str]):
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

    slurm = SlurmCommand(args, SlurmModel())
    if slurm.help:
        print_help(script, SlurmModel(), kbatch.__doc__) # type: ignore
        exit()
    command = slurm.command if slurm.command else f"{Fore.RED}Must provide a command"

    print(txt.KBATCH_MSG.format(slurm_args=slurm.slurm_args, command=command))
    if slurm.command:
        output = subprocess\
            .run(slurm.batch, shell=True, capture_output=True)\
            .stdout.decode()

        if slurm.test:
            # output will be the issued command, so we print it
            print(Fore.WHITE + output)
        else:
            # We subtract the last character of the output
            # to remove the final "\n" character and get the 
            # job_id
            slurmid = output[:-1]

            print(f"""Scheduled job {slurmid}.
    To cancel, run:
        scancel {slurmid}
        """)

def main():
    kbatch(sys.argv[0], sys.argv[1:])