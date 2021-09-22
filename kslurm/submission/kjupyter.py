from __future__ import absolute_import

import re
import signal
import subprocess
import sys
from typing import List

import kslurm.text as txt
from kslurm.args import print_help
from kslurm.models import SlurmModel
from kslurm.slurm import SlurmCommand
from kslurm.style.console import console


def kjupyter(script: str, args: List[str]):
    """Start a Jupyter session

    Begins a Jupyter session on an interactive node. By default, it requests 3hr. No
    more time than this should be requested, as this could significantly delay the
    start of the server.

    For the command to work, a virtualenv containing jupyter-lab should already be
    activated. Use `pip install jupyter-lab`
    """
    slurm = SlurmCommand(args, SlurmModel())
    if slurm.help:
        print_help(script, SlurmModel(), kjupyter.__doc__)  # type: ignore
        exit()

    slurm.command = ["jupyter-lab", "--ip", "$(hostname -f)", "--no-browser"]
    print(txt.KRUN_CMD_MESSAGE.format(args=slurm.slurm_args, command=slurm.command))

    if not slurm.test:

        proc = subprocess.Popen(
            slurm.run,
            shell=True,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        jobid = "0"

        def signal_handler(*args):  # type: ignore
            subprocess.run(f"scancel {jobid}", shell=True)
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)  # type: ignore

        while proc.poll() is None:
            if proc.stdout:
                line = proc.stdout.readline().decode().strip()
                queued = re.match(
                    r"^srun: job (\d+) queued and waiting for resources", line
                )
                url = re.match(
                    r"^https?:\/\/((?:[\w-]+\.)+(?:[\w]+)):(\d+)(\/lab\?token=\w+)$",
                    line,
                )
                if queued:
                    jobid = queued.group(1)
                elif any(
                    [
                        re.match(r"^srun: job \d+ has been allocated resources", line),
                        re.match(
                            r"^To access the server, open this file in a browser:$",
                            line,
                        ),
                        re.match(r"^file:\/\/\/(?:[\w.\-_]+\/)+[\w.\-_]+\.html$", line),
                        re.match(r"^Or copy and paste one of these URLs:$", line),
                        re.match(
                            r"^or http:\/\/(?:[\d]+\.)+\d+:\d+\/lab\?token=\w+$", line
                        ),
                    ]
                ):
                    pass
                elif url:
                    domain = url.group(1)
                    port = url.group(2)
                    path = url.group(3)
                    console.print(
                        txt.JUPYTER_WELCOME.format(
                            port=port, domain=domain, path=path, url=url.group(0)
                        )
                    )
                else:
                    print(line)


def main():
    kjupyter(sys.argv[0], sys.argv[1:])


if __name__ == "__main__":
    main()
