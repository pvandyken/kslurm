import sys, subprocess
from colorama import Fore
from cluster_utils.slurm import SlurmCommand
from cluster_utils.slurm import ArgList

def main():
    slurm = SlurmCommand(sys.argv[1:], ArgList())
    print(f"{Fore.GREEN}Running interactive session with {Fore.WHITE + slurm.slurm_args}")
    subprocess.run(slurm.interactive, shell=True)

if __name__ == "__main__":
    main()