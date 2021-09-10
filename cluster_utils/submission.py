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
        # We pre-resolve the command for full transparency
        resolved_command = subprocess\
            .run(f"echo \"{slurm.command}\"", shell=True, capture_output=True)\
            .stdout.decode()
        command_msg = "\n".join([
            slurm.command, 
            f"{Fore.LIGHTBLUE_EX}resolved as {Fore.RESET}", 
            resolved_command
        ])
        print(txt.KRUN_CMD_MESSAGE.format(args=slurm.slurm_args, command=command_msg))
    else:
        print(txt.INTERACTIVE_MSG.format(args=slurm.slurm_args))

    if not slurm.test:
        subprocess.run(slurm.run, shell=True)

def kalloc():
    slurm = SlurmCommand(sys.argv[1:], ArgList())
    if slurm.command:
        print(txt.KALLOC_MSG.format(args=slurm.slurm_args, command=slurm.command))
    else:
        print(txt.INTERACTIVE_MSG.format(args=slurm.slurm_args))
    if not slurm.test:
        subprocess.run(slurm.alloc, shell=True)

