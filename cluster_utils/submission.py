import sys, subprocess
from colorama import Fore

from cluster_utils.slurm import SlurmCommand
from cluster_utils.slurm import ArgList
from . import text as txt

def kbatch():
    slurm = SlurmCommand(sys.argv[1:], ArgList())
    command = slurm.command if slurm.command else f"{Fore.RED}Must provide a command"

    print(txt.KBATCH_MSG.format(slurm_args=slurm.slurm_args, command=command))
    if slurm.command:
        subprocess.run(slurm.batch, shell=True)

def krun():
    slurm = SlurmCommand(sys.argv[1:], ArgList())
    if slurm.command:
        print(txt.KRUN_CMD_MESSAGE.format(args=slurm.slurm_args, command=slurm.command))
    else:
        print(txt.INTERACTIVE_MSG.format(args=slurm.slurm_args))

    if not slurm.test:
        subprocess.run(slurm.run, shell=True)

