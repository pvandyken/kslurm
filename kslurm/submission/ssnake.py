from __future__ import absolute_import

import itertools as it
import subprocess
import sys
from pathlib import Path

import attr
from colorama import Fore, Style

from kslurm.args.arg_types import PositionalArg
from kslurm.exceptions import ValidationError
from kslurm.models import SlurmModel
from kslurm.slurm import SlurmCommand


# Helper function for formatting the list of settings in our output
def setting_list(name: str, setting: str) -> str:
    return (
        Fore.YELLOW
        + name
        + ": "
        + Fore.WHITE
        + Style.BRIGHT
        + setting
        + Style.RESET_ALL
    )


def profile_validator(profile: str) -> str:
    profile_path = Path.home() / ".config" / "snakemake"
    configfiles = [profile_path.glob(f"*/config.{ext}") for ext in ["yml", "yaml"]]
    profiles = [configfile.parent.name for configfile in it.chain(*configfiles)]
    if profile in profiles:
        return profile
    if profiles:
        profiles = "\n".join(profiles)
        profilelist = f"Found the following profiles:\n{profiles}"
    else:
        profilelist = f"Did not find any valid profiles in {profile_path}"
    raise ValidationError(
        f'{Fore.RED}"{Fore.LIGHTRED_EX + profile + Fore.RED}" '
        f"is not a valid profile.{Fore.RESET} \n\n{profilelist}"
    )


# Extended Model
@attr.s(auto_attribs=True)
class SSnakeModel(SlurmModel):
    profile: PositionalArg[str] = PositionalArg(validator=profile_validator)


def main():
    models = SSnakeModel()
    models.cpu.value = "2"
    models.profile
    slurm = SlurmCommand(sys.argv[1:], models)

    # Get the profile
    profile = slurm.args.profile.value

    # Use parent directory name as the job name
    slurm.name = Path.cwd().name
    slurm.output = "snakemake-%j.out"

    # Update our submission script
    slurm.script = [
        "source $SNAKEMAKE_VENV_DIR/activate",
        "panoptes --ip $(hostname -f) 1> panoptes.out 2>&1 &",
        "PANOPTES_PID=$!",
        '(tail -F panoptes.out & ) | grep -q "Running on"',
        "hostname -f",
        'snakemake --wms-monitor "http://$(hostname -f):5000" '
        f"--profile {profile} {slurm.command}",
        "kill $PANOPTES_PID",
        "rm panoptes.out",
    ]

    # Run the process and collect the jobid output.
    output = subprocess.run(
        slurm.batch, shell=True, capture_output=True
    ).stdout.decode()

    if slurm.test:
        # output will be the issued command, so we print it
        print(Fore.WHITE + output)
    else:
        # We subtract the last 2 characters of the output
        # to remove the final "\n" characters and get the
        # job_id
        slurmid = output[:-2]

        # Print a helpful confirmation message
        print(
            f"""
    {Fore.GREEN}Scheduling Snakemake
        {Fore.LIGHTBLUE_EX}SETTINGS
            {Fore.WHITE}{slurm.slurm_args}

            {setting_list("profile", profile)}
            {setting_list("job_name", slurm.name)}
            {setting_list("job_id", slurmid)}
            {setting_list("other_args", slurm.command)}

    To cancel the job, run:
        scancel {slurmid}
        """
        )


if __name__ == "__main__":
    main()
