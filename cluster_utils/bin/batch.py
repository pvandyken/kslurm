#!/usr/bin/env python
import sys, subprocess
from colorama import Fore

from cluster_utils.utils.slurm_args import SlurmCommand

def main():

    slurm = SlurmCommand(sys.argv[1:])
    command = slurm.command if slurm.command else f"{Fore.RED}Must provide a command"

    print(f"""
    {Fore.GREEN}Scheduling Batch Command
        {Fore.LIGHTBLUE_EX}SETTINGS
            {Fore.WHITE}{slurm.slurm_args}
        {Fore.LIGHTBLUE_EX}COMMAND
            {Fore.WHITE}{command}
    """)
    if slurm.command:
        subprocess.run(slurm.batch, shell=True)

if __name__ == "__main__":
    main()