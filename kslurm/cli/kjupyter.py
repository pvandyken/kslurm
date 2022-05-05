from __future__ import absolute_import

import importlib.resources as impr
import re
import signal
import subprocess
import subprocess as sp
import sys
from typing import Union

import attr

import kslurm.text as txt
from kslurm.args import keyword
from kslurm.args.command import ParsedArgs, command
from kslurm.exceptions import TemplateError
from kslurm.models.slurm import SlurmModel
from kslurm.slurm.slurm_command import SlurmCommand
from kslurm.style.console import console
from kslurm.venv import VenvCache


@attr.frozen
class JupyterModel(SlurmModel):
    venv: list[str] = keyword(["--venv"])


@command(terminate_on_unknown=True)
def kjupyter(
    args: Union[JupyterModel, TemplateError],
    command_args: list[str],
    arglist: ParsedArgs,
):
    """Start a Jupyter session

    Begins a Jupyter session on an interactive node. By default, it requests 3hr. No
    more time than this should be requested, as this could significantly delay the
    start of the server.

    The --venv arg can be used to specify saved venv. This venv must already
    have jupyter-lab installed, or the command will fail. This will install the
    venv into local scratch, and will thus lead to the best performance.
    Alternatively, you can run the in an already activated virtualenv containing
    jupyter-lab.
    """
    slurm = SlurmCommand(args, command_args, arglist)
    assert isinstance(args, JupyterModel)

    if args.venv:
        venv_cache = VenvCache()
        if args.venv[0] not in venv_cache:
            print("Valid venvs:\n" + str(venv_cache))
            return 1

    with impr.path("kslurm.bin", "kpy-wrapper.sh") as path:
        cmd = [
            "jupyter-lab",
            "--ip",
            "$(hostname -f)",
            "--no-browser",
        ]
        print(txt.KRUN_CMD_MESSAGE.format(args=slurm.slurm_args, command=" ".join(cmd)))
        slurm.command = [
            *(
                [
                    "source",
                    str(path),
                    "&&",
                    "kpy",
                    "load",
                    args.venv[0],
                    "&&",
                ]
                if args.venv
                else []
            ),
            *cmd,
        ]

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
                    try:
                        hostname = sp.run(
                            ["wget", "-qO-", "ipinfo.io/ip"], capture_output=True
                        ).stdout.decode().strip()
                    except RuntimeError:
                        hostname = "<hostname>"
                    console.print(
                        txt.JUPYTER_WELCOME.format(
                            port=port,
                            domain=domain,
                            path=path,
                            url=url.group(0),
                            username=sp.run(
                                ["whoami"], capture_output=True
                            ).stdout.decode().strip(),
                            hostname=hostname,
                        )
                    )
                else:
                    print(line)


if __name__ == "__main__":
    kjupyter()
