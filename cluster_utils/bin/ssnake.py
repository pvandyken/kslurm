#!/usr/bin/env python
import sys, subprocess
from pathlib import Path
from colorama import Fore, Style

from cluster_utils.utils.slurm_args import SlurmCommand
import cluster_utils.utils.toolz_stub as tz

# def get_config_path(name):
#     candidates = [
#         Path(parent, name).with_suffix(suffix) 
#             for parent in [".", "config"] 
#                 for suffix in [".yaml", ".yml"]
#     ]
#     exist = [c.exists() for c in candidates]
#     if any(exist):
#         return tz.second(
#                 tz.first(
#                 filter(lambda x: tz.first(x),
#                 zip(exist, candidates)
#         )))
#     else:
#         return None

# Helper function for formatting the list of settings in our output
def setting_list(name, setting):
    return Fore.YELLOW + name + ": " + Fore.WHITE + Style.BRIGHT + setting + Style.RESET_ALL

def main():
    slurm = SlurmCommand(sys.argv[1:], cpu=2)
    if len(slurm.command_list) < 1:
        print(f"{Fore.RED}Must provide a profile")
        exit()

    # Get the profile and check if it exists before submission
    profile = slurm.command_list[0]
    if not any([(Path.home() / ".config" / "snakemake" / "slurm" / "config").with_suffix(s).exists() for s in ['.yml', '.yaml']]):
        print(f"{Fore.RED}\"{Fore.LIGHTRED_EX + profile + Fore.RED}\" is not a valid profile")
        if not slurm.test:
            sys.exit(1)
    
    args = slurm.command_list[1:]

    # Use parent directory name as the job name
    slurm.name = Path.cwd().name
    slurm.output = "snakemake-%j.out"

    # Update our submission script
    slurm.submit_script = [
        "source $SNAKEMAKE_VENV_DIR/activate",
        "panoptes --ip $(hostname -f) 1> panoptes.out 2>&1 &",
        "PANOPTES_PID=$!",
        "(tail -F panoptes.out & ) | grep -q \"Running on\"",
        "hostname -f",
        f"snakemake --wms-monitor \"http://$(hostname -f):5000\" --profile {profile} {' '.join(args)}",
        "kill $PANOPTES_PID",
        "rm panoptes.out"
    ]

    # Run the process and collect the jobid output. 
    output = subprocess\
        .run(f"{slurm.batch}", shell=True, capture_output=True)\
        .stdout.decode()

    if slurm.test:
        # output will be the issued command, so we print it
        print(Fore.WHITE + output)
    else:
        # We subtract the last 2 characters of the output
        # to remove the final "\n" characters and get the 
        # job_id
        slurmid = output[:-2]

        # Print a helpful confirmation message
        print(f"""
    {Fore.GREEN}Scheduling Snakemake
        {Fore.LIGHTBLUE_EX}SETTINGS
            {Fore.WHITE}{slurm.slurm_args}

            {setting_list("profile", profile)}
            {setting_list("job_name", slurm.name)}
            {setting_list("job_id", slurmid)}
            {setting_list("other_args", ' '.join(args)) if args else ''}
    
    To cancel the job, run:
        scancel {slurmid}
        """) 

if __name__ == "__main__":
    main()