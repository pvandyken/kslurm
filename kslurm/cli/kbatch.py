from __future__ import absolute_import

import datetime as dt
import re
import subprocess
from typing import Union

from colorama import Fore

import kslurm.text as txt
from kslurm.args.command import Parsers, command
from kslurm.exceptions import TemplateError
from kslurm.models.slurm import SlurmModel
from kslurm.slurm.slurm_command import SlurmCommand
from kslurm.style import console


@command(terminate_on_unknown=True)
def kbatch(
    args: Union[SlurmModel, TemplateError],
    command_args: list[str],
    arglist: Parsers,
):
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

    slurm = SlurmCommand(args, command_args, arglist)
    command = slurm.command if slurm.command else f"{Fore.RED}Must provide a command"

    console.print(txt.KBATCH_MSG.format(slurm_args=slurm.slurm_args, command=command))
    if slurm.command:
        test = subprocess.run(slurm.batch_test, shell=True, capture_output=True)

        proc = subprocess.run(
            slurm.batch, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
        )

        out = proc.stdout.decode()

        if proc.returncode != 0:
            print(Fore.WHITE + out)
            return 1
        if slurm.test:
            # output will be the issued command, so we print it
            print(Fore.WHITE + out)

        if test.returncode == 0 and (
            match := re.search(
                r"(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})T"
                r"(?P<hour>\d{2}):(?P<minute>\d{2}):(?P<second>\d{2})",
                test.stderr.decode(),
            )
        ):
            startdate = dt.datetime(
                **{key: int(value) for key, value in match.groupdict().items()}
            )
            now = dt.datetime.now()
            delta = startdate - now

            prefix = "at"
            # If at least 7am tomorrow
            if delta.total_seconds() > 16 * 60 * 60 and startdate.date() != now.date():
                if startdate.date() == now.date() + dt.timedelta(days=1):
                    date = " tomorrow"
                elif startdate.date() < now.date() + dt.timedelta(days=6):
                    date = f" on {startdate.strftime('%A')}"
                else:
                    date = f" on {startdate.strftime('%a, %b %d')}"
            else:
                date = ""
            time = startdate.strftime("%I:%M%p")

            ddhr, mn = divmod(int(max(0, delta.total_seconds())) // 60, 60)
            day, hr = divmod(ddhr, 24)
            _fromnow = ",".join(
                filter(
                    None,
                    [
                        f"{day}d" if day else None,
                        f"{hr}h" if day or hr else None,
                        f"{mn}m" if day or hr or mn else None,
                    ],
                )
            )
            fromnow = f"({_fromnow} from now)" if _fromnow else "(immediately)"
        else:
            prefix = ""
            date = ""
            time = ""
            fromnow = ""

        if slurm.test:
            print(
                f"""Estimated start time {prefix} {Fore.BLUE}{time}{date} \
{Fore.LIGHTRED_EX}{fromnow}
"""
            )
            return
        slurmid = out.strip()
        print(
            f"""Scheduled job {Fore.LIGHTBLACK_EX}{slurmid}
    {Fore.WHITE}Estimated start {prefix} {Fore.BLUE}{time}{date} \
{Fore.LIGHTRED_EX}{fromnow}
    {Fore.WHITE}To cancel, run:
        scancel {slurmid}
        """
        )


if __name__ == "__main__":
    kbatch.cli(["kbatch", "--account", "foo", "-t"])
