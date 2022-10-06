from __future__ import absolute_import

import importlib.resources as impr
import os
import re
import signal
import subprocess as sp
import sys
import tempfile as tmp
from pathlib import Path
from typing import Any, Union

import attrs

import kslurm.bin
import kslurm.text as txt
from kslurm.args import HelpRequest, InvalidSubcommand, Subcommand, subcommand
from kslurm.args.arg_types import keyword
from kslurm.args.command import CommandError, Parsers, command
from kslurm.args.help import HelpText
from kslurm.exceptions import TemplateError
from kslurm.models.slurm import SlurmModel
from kslurm.slurm.slurm_command import SlurmCommand
from kslurm.style import console
from kslurm.venv import VenvCache


@attrs.frozen
class KjupyterEnv:
    active: bool
    logs: Path

    @staticmethod
    def get_env_var(name: str):
        return "_KJUPYTER_" + name

    def export(self):
        for field, value in attrs.asdict(self).items():
            os.environ[self.get_env_var(field)] = str(value or "")

    @classmethod
    def load(cls):
        fields = attrs.fields(cls)
        vals = {
            field.name: field.type(val)
            if (val := os.environ.get(cls.get_env_var(field.name))) is not None
            else field.type()
            for field in fields
            if field.type is not attrs.NOTHING and field.type is not None
        }
        return cls(**vals)


@command(terminate_on_unknown=True)
def _kjupyter(
    args: Union[SlurmModel, TemplateError],
    command_args: list[str],
    arglist: Parsers,
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
    slurm.name = "jupyter"
    assert isinstance(args, SlurmModel)

    # slurm.set_venv("")

    if args.venv:
        venv_cache = VenvCache()
        if args.venv not in venv_cache:
            print("Valid venvs:\n" + str(venv_cache))
            return 1

    env = KjupyterEnv(active=True, logs=Path(tmp.mkstemp(prefix="kjupyter_logs.")[1]))

    cmd = [
        "jupyter-lab",
        "--ip",
        "$(hostname -f)",
        "--no-browser",
        "2>&1",
        "|",
        "tee",
        str(env.logs),
    ]
    console.print(
        txt.KRUN_CMD_MESSAGE.format(args=slurm.slurm_args, command=" ".join(cmd))
    )
    # venv_load = ["source", str(path), "; kpy load", args.venv] if args.venv else []
    with impr.path(kslurm.bin, "kpy-wrapper.sh") as path:
        slurm.command = (
            [
                "command -v jupyter-lab > /dev/null || (echo 'jupyter-lab not found, "
                "attempting install' && pip install jupyterlab);",
                *cmd,
            ]
            if args.venv
            else cmd
        )

    if slurm.test:
        print(slurm.run)
        return

    proc = sp.Popen(
        slurm.run,
        shell=True,
        stdin=sp.PIPE,
        stdout=sp.PIPE,
        stderr=sp.STDOUT,
    )
    jobid = "0"

    def signal_handler(*args: Any):
        sp.run(f"scancel {jobid}", shell=True)
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

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
                        r"^To access the server, open this file in a browser:$", line
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
                    hostname_proc = sp.run(
                        ["wget", "-qO-", "ipinfo.io/ip"], capture_output=True
                    )
                    hostname_proc.check_returncode()
                    hostname = hostname_proc.stdout.decode().strip()
                except (RuntimeError, sp.CalledProcessError):
                    hostname = "<hostname>"
                console.print(
                    txt.JUPYTER_WELCOME.format(
                        port=port,
                        domain=domain,
                        path=path,
                        url=url.group(0),
                        username=sp.getoutput("whoami").strip(),
                        hostname=hostname,
                    )
                )
                sp.run(
                    [
                        "srun",
                        f"--jobid={jobid}",
                        "--pty",
                        "bash",
                        "-c",
                        slurm.venv_activate + " bash -i",
                    ]
                )
            # else:
            #     print(line)


@command(inline=True)
def _log(lines: int = keyword(["-n", "--lines"], default=20)):
    env = KjupyterEnv.load()
    lines_arg = ["--lines", str(lines)]
    sp.run(["tail", env.logs, *lines_arg])


@command(inline=True)
def _console():
    sp.run(["jupyter", "console", "--use-existing"])


@attrs.frozen
class _JupyterModel:
    cmd: Subcommand = subcommand({"log": _log, "console": _console}, default=_kjupyter)


@command
def kjupyter(
    entrypoint: str,
    args: Union[_JupyterModel, InvalidSubcommand, HelpRequest],
    command_args: list[str],
    helptext: HelpText,
):
    """Placeholder docstring"""
    env = KjupyterEnv.load()
    if isinstance(args, HelpRequest):
        if env.active:
            console.print(helptext)
        else:
            console.print(_kjupyter.get_helptext(entrypoint))
        return
    if isinstance(args, InvalidSubcommand):
        if env.active:
            console.print(args.args[0])
            return
        return _kjupyter.cli(["kjupyter", *command_args])
    name, func = args.cmd
    if not name:
        return func([name, *command_args])
    entry = f"{entrypoint} {name}"
    if not env.active:
        raise CommandError(
            f"The '{name}' command is only available in a running jupyter notebook"
        )
    return func([entry, *command_args])


if __name__ == "__main__":
    # KjupyterEnv(True, Path("./poetry.lock")).export()
    kjupyter.cli(["kjupyter", "--account", "foo", "--venv", "test", "-t"])
