import sys, subprocess
from colorama import Fore

from cluster_utils.slurm import SlurmCommand
from cluster_utils.slurm import ArgList

settings_header = f"{Fore.LIGHTBLUE_EX}SETTINGS{Fore.RESET}"
command_header = f"{Fore.LIGHTBLUE_EX}COMMAND{Fore.RESET}"

def kbatch():
    slurm = SlurmCommand(sys.argv[1:], ArgList())
    command = slurm.command if slurm.command else f"{Fore.RED}Must provide a command"

    print(f"""
    {Fore.GREEN}Scheduling Batch Command
        {settings_header}
            {Fore.WHITE}{slurm.slurm_args}
        {command_header}
            {Fore.WHITE}{command}
    """)
    if slurm.command:
        subprocess.run(slurm.batch, shell=True)

def krun():
    slurm = SlurmCommand(sys.argv[1:], ArgList())
    if slurm.command:
        resolved_command = subprocess\
            .run(f"echo \"{slurm.command}\"", shell=True, capture_output=True)\
            .stdout.decode()
        print(f"""
    {Fore.GREEN}Running job 
        {settings_header}
            {Fore.WHITE + slurm.slurm_args}
        {command_header}
            {slurm.command}""")
        if resolved_command != slurm.command:
            print(f"""
            {Fore.LIGHTBLUE_EX}resolved as{Fore.RESET}
            {resolved_command}""")
    else:
        print(f"""
    {Fore.GREEN}Running interactive session
        {settings_header}
            {Fore.WHITE + slurm.slurm_args}
        """)

    if not slurm.test:
        subprocess.run(slurm.run, shell=True)

def kalloc():
    slurm = SlurmCommand(sys.argv[1:], ArgList())
    if slurm.command:
        print(f"""
    {Fore.GREEN}Running job as script 
        {settings_header}
            {Fore.WHITE + slurm.slurm_args}
        {command_header}
            {slurm.command}
        """)
    else:
        print(f"""
    {Fore.GREEN}Running interactive session
        {settings_header}
            {Fore.WHITE + slurm.slurm_args}
        """)
    if not slurm.test:
        subprocess.run(slurm.alloc, shell=True)

