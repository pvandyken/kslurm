from __future__ import absolute_import

import importlib.resources as impr
import json
import os
import re
import signal
import subprocess as sp
import sys
import tempfile as tmp
from pathlib import Path
from typing import Any, Union

import attrs
from yaspin import yaspin

import kslurm.bin
import kslurm.text as txt
from kslurm.args import HelpRequest, InvalidSubcommand, Subcommand, subcommand
from kslurm.args.arg_types import choice, flag, keyword
from kslurm.args.command import CommandError, Parsers, command
from kslurm.args.help import HelpText
from kslurm.exceptions import TemplateError
from kslurm.models.slurm import SlurmModel
from kslurm.slurm.slurm_command import SlurmCommand
from kslurm.style import console
from kslurm.venv import VenvCache


@attrs.frozen
class _KjupyterEnv:
    active: bool
    logs: Path
    domain: str = ""
    hostname: str = ""
    username: str = ""
    port: str = ""
    token: str = ""
    url: str = ""

    @staticmethod
    def get_env_var(name: str):
        return "_KJUPYTER_" + name

    def export(self):
        for field, value in attrs.asdict(self).items():
            os.environ[self.get_env_var(field)] = str(value or "")

    def set_server_vals(
        self, hostname: str, username: str, port: str, token: str, url: str, domain: str
    ):
        return attrs.evolve(
            self,
            hostname=hostname,
            username=username,
            port=port,
            token=token,
            url=url,
            domain=domain,
        )

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


@attrs.frozen
class _KjupyterExtendedModel(SlurmModel):
    debug: bool = flag(["--debug"])


_KjupyterExtendedModel.__doc__ = SlurmModel.__doc__


def _get_tunnel_script(*, port: str, domain: str, username: str, hostname: str):
    return f"ssh -L {port}:{hostname}:{port} {username}@{domain}"


def _get_browser_url(*, port: str, token: str):
    return f"http://localhost:{port}/lab?token={token}"


@command(terminate_on_unknown=True, allow_unknown=False)
def _kjupyter(
    args: Union[_KjupyterExtendedModel, TemplateError],
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
    slurm = SlurmCommand(args, [], arglist)
    slurm.name = "jupyter"
    assert isinstance(args, SlurmModel)

    if args.venv:
        venv_cache = VenvCache()
        if args.venv not in venv_cache:
            print("Valid venvs:\n" + str(venv_cache))
            return 1

    env = _KjupyterEnv(active=True, logs=Path(tmp.mkstemp(prefix="kjupyter_logs.")[1]))
    env.export()

    cmd = [
        "jupyter-lab",
        "--ip",
        "$(hostname -f)",
        "--no-browser",
        "-y",
        "2>&1",
        "|",
        "tee",
        str(env.logs),
    ]
    console.print(
        txt.KRUN_CMD_MESSAGE.format(args=slurm.slurm_args, command=" ".join(cmd))
    )
    # venv_load = ["source", str(path), "; kpy load", args.venv] if args.venv else []
    with impr.path(kslurm.bin, "kpy-wrapper.sh") as token:
        slurm.command = (
            [
                "command -v jupyter-lab > /dev/null || (echo 'jupyter-lab not found' "
                "&& pip install jupyterlab);",
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

    port = None
    with yaspin(text="Acquiring resources") as spinner:
        if args.debug:
            spinner.stop()
        while proc.poll() is None:
            if proc.stdout:
                line = proc.stdout.readline().decode().strip()
                queued = re.match(
                    r"^srun: job (\d+) queued and waiting for resources", line
                )
                url = re.match(
                    r"^https?:\/\/((?:[\w-]+\.)+(?:[\w]+)):(\d+)\/lab\?token=(\w+)$",
                    line,
                )

                # unused code to grab the address lines
                _ = any(
                    [
                        re.match(
                            r"^To access the server, open this file in a browser:$",
                            line,
                        ),
                        re.match(r"^file:\/\/\/(?:[\w.\-_]+\/)+[\w.\-_]+\.html$", line),
                        re.match(r"^Or copy and paste one of these URLs:$", line),
                        re.match(
                            r"^or http:\/\/(?:[\d]+\.)+\d+:\d+\/lab\?token=\w+$",
                            line,
                        ),
                    ]
                )

                if queued:
                    jobid = queued.group(1)

                elif re.match(r"^Unpacking venv \'.+\'", line):
                    spinner.text = "Unpacking venv"
                    if args.debug:
                        print(line)

                elif re.match(r"jupyter-lab not found", line):
                    spinner.text = "Installing jupyter-lab"
                    if args.debug:
                        print(line)

                elif url:
                    hostname = url.group(1)
                    port = url.group(2)
                    token = url.group(3)
                    username = sp.getoutput("whoami").strip()
                    try:
                        domain = (
                            sp.check_output(["wget", "-qO-", "ipinfo.io/ip"])
                            .decode()
                            .strip()
                        )
                    except (RuntimeError, sp.CalledProcessError):
                        domain = "<hostname>"
                    env.set_server_vals(
                        hostname=hostname,
                        username=username,
                        port=port,
                        token=token,
                        url=url.group(0),
                        domain=domain,
                    ).export()
                    spinner.text = "Finished!"
                    if not args.debug:
                        spinner.ok("🚀")
                        console.print(
                            txt.JUPYTER_WELCOME.format(
                                browser_url=_get_browser_url(port=port, token=token),
                                tunnel_script=_get_tunnel_script(
                                    port=port,
                                    domain=domain,
                                    username=username,
                                    hostname=hostname,
                                ),
                                url=url.group(0),
                            )
                        )
                        break

                elif args.debug:
                    print(line)

        assert port
        sp.run(
            [
                "srun",
                f"--jobid={jobid}",
                "--pty",
                "--overlap",
                "bash",
                "-c",
                slurm.venv_activate + " bash",
            ]
        )
        with yaspin(text="Shutting down jupyter") as spinner:
            sp.run(
                [
                    "srun",
                    f"--jobid={jobid}",
                    "--overlap",
                    "bash",
                    "--noprofile",
                    "--norc",
                    "-c",
                    slurm.venv_activate + f" jupyter lab stop {port}",
                ],
                capture_output=True,
            )
            spinner.ok()


@command(inline=True)
def _log(lines: int = keyword(["-n", "--lines"], default=20)):
    """Display the logs from the jupyter session

    Args:
        lines: Number of lines to display (default 20)
    """
    env = _KjupyterEnv.load()
    lines_arg = ["--lines", str(lines)]
    proc = sp.Popen(["tail", env.logs, *lines_arg], stdout=sp.PIPE)
    while proc.poll() is None:
        if proc.stdout:
            for line in proc.stdout.readlines():
                console.print(line.decode().rstrip(), markup=False)


@command(inline=True)
def _console():
    """Begin interactive python console

    The jupyter-console package must already be installed in the virtual env. A kernel
    must already be started by a notebook file
    """
    env = _KjupyterEnv.load()
    sessions = json.loads(
        sp.check_output(
            [
                "curl",
                "-sSLG",
                f"{env.hostname}:{env.port}/api/sessions",
                "--data-urlencode",
                f"token={env.token}",
            ]
        )
    )
    if not len(sessions):
        raise CommandError(
            "No sessions found. Activate a jupyter notebook before running this "
            "command."
        )
    sp.run(["jupyter", "console", "--existing"])


@command(inline=True)
def _url(
    format: str = choice(
        ["browser", "server"],
    )
):
    """Echo the jupyter server url

    Args:
        format: The url format to retrieve: browser for the webapp, and server for
            vscode
    """
    env = _KjupyterEnv.load()
    if format == "browser":
        print(_get_browser_url(port=env.port, token=env.token))
        return 0
    print(env.url)


@command(inline=True)
def _tunnel():
    """Echo the bash code to open an ssh tunnel to the jupyter server"""
    env = _KjupyterEnv.load()
    print(
        _get_tunnel_script(
            port=env.port,
            domain=env.domain,
            username=env.username,
            hostname=env.hostname,
        )
    )


@attrs.frozen
class _JupyterModel:
    cmd: Subcommand = subcommand(
        {"log": _log, "console": _console, "url": _url, "tunnel": _tunnel},
        default=_kjupyter,
    )


@command
def kjupyter(
    entrypoint: str,
    args: Union[_JupyterModel, InvalidSubcommand, HelpRequest],
    command_args: list[str],
    helptext: HelpText,
):
    """Helper commands to manage jupyter session

    To close the jupyter server, press CTRL-D or run `exit`
    """
    env = _KjupyterEnv.load()
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
            f"The '{name}' command is only available in a running jupyter notebook. "
            "Use the kjupyter base command to start a new notebook session"
        )
    return func([entry, *command_args])


if __name__ == "__main__":
    # KjupyterEnv(True, Path("./poetry.lock")).export()
    kjupyter.cli(["kjupyter", "url", "--help"])
