import attr
from cluster_utils.args.arg_types import PositionalArg
import sys, subprocess
from pathlib import Path
from colorama import Fore, Style

from cluster_utils.slurm import SlurmCommand, ArgList

# Helper function for formatting the list of settings in our output
def setting_list(name: str, setting: str) -> str:
    return Fore.YELLOW + name + ": " + Fore.WHITE + Style.BRIGHT + setting + Style.RESET_ALL

def profile_validator(profile: str) -> bool:
    profile_path = Path.home() / ".config" / "snakemake" / "slurm" / "config" / profile
    if any([profile_path.with_suffix(s).exists() for s in ['.yml', '.yaml']]):
        print(f"{Fore.RED}\"{Fore.LIGHTRED_EX + profile + Fore.RED}\" is not a valid profile")
        return True
    return False

# Extended Model
@attr.s(auto_attribs=True)
class SSnakeModel(ArgList):
    profile: PositionalArg = PositionalArg()

def main():
    models = SSnakeModel()
    models.cpu.value = "2"
    models.profile 
    slurm = SlurmCommand(sys.argv[1:], models)

    # Get the profile and check if it exists before submission
    profile = str(slurm.args.profile)
    profile_path = Path.home() / ".config" / "snakemake" / "slurm" / "config" / profile
    if not any([profile_path.with_suffix(s).exists() for s in ['.yml', '.yaml']]):
        print(f"{Fore.RED}\"{Fore.LIGHTRED_EX + profile + Fore.RED}\" is not a valid profile")
        if not slurm.test:
            sys.exit(1)
    
    

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
        f"snakemake --wms-monitor \"http://$(hostname -f):5000\" --profile {profile} {slurm.command}",
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
            {setting_list("other_args", slurm.command)}
    
    To cancel the job, run:
        scancel {slurmid}
        """) 

if __name__ == "__main__":
    main()