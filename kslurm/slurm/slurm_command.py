from __future__ import absolute_import, annotations

import importlib.resources as impr
import os
import shlex
import sys
from pathlib import Path
from typing import List, Union

import kslurm.appconfig as appconfig
import kslurm.bin
import kslurm.models.job_templates as templates
import kslurm.slurm.helpers as helpers
from kslurm.args.command import Parsers
from kslurm.exceptions import TemplateError, ValidationError
from kslurm.models.slurm import SlurmModel

_LOAD_ENV = (
    "[[ -e $HOME/.bashrc ]] && source $HOME/.bashrc; "
    "source {path}; kpy {method} {name};"
)


class SlurmCommand:
    def __init__(
        self,
        args: Union[SlurmModel, TemplateError],
        tail: list[str],
        arglist: Parsers,
    ):
        self._name = ""
        self._output = ""

        if isinstance(args, TemplateError):
            print(args.msg)
            print("Choose from the following list of templates:\n")
            templates.list_templates()
            exit(1)

        assert isinstance(args, SlurmModel)
        if args.list_job_templates:
            templates.list_templates()
            exit()

        # set_template returns templated values only if a template is passed
        # if we pass a blank string, the models are returned unchanged
        template_vals = templates.set_template(
            args.job_template, mem=args.mem, cpu=args.cpu, time=args.time
        )

        # Start by setting these three with model/template
        self.time = template_vals.time
        self.cpu = template_vals.cpu
        self.mem = template_vals.mem

        # Then update if values were specifically supplied on the command line
        if arglist["time"].value is not None:
            self.time = args.time
        if arglist["cpu"].value is not None:
            self.cpu = args.cpu
        if arglist["mem"].value is not None:
            self.mem = args.mem

        self.gpu = bool(args.gpu)
        self.x11 = bool(args.x11)
        config = appconfig.Config()
        if not args.account:
            if self.gpu:
                account = config.get("account.gpu")
            else:
                account = config.get("account.cpu")
            if account is None:
                account = config.get("account")
            if not account:
                print(
                    "Account must either be specified using --account, or provided in "
                    "config. A default account can be added to config by running "
                    "kslurm config account <account_name>"
                )
                sys.exit(1)
            self.account = account
        else:
            self.account = args.account
        self.cwd = args.directory
        self.test = args.test
        self.job_template = args.job_template
        self._command = tail

        os.chdir(self.cwd)

        self.args = args
        self._venv = args.venv or None

    ###
    # Job Paramaters
    ###
    @property
    def time(self):
        return helpers.slurm_time_format(self._time)

    @time.setter
    def time(self, time: int):
        self._time = time

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name: str):
        self._name = name

    @property
    def output(self):
        return self._output

    @output.setter
    def output(self, output: str):
        self._output = f'--output="{output}"'

    def set_venv(self, name: str):
        self._venv = name

    ###
    # Command line strings
    ###
    @property
    def slurm_args(self):
        s = (
            f"--account={self.account} --time={self.time} "
            f"--cpus-per-task={self.cpu} --mem={self.mem}"
        )
        if self.gpu:
            s += " --gres=gpu:1"
        if self.x11:
            s += " --x11"
        if self.name:
            s += f" --job-name='{self.name}'"
        return s

    @property
    def command(self):
        return " ".join(self._command)

    @command.setter
    def command(self, commands: List[str]):
        self._command = commands

    @property
    def script(self):
        return "\n".join(["#!/bin/bash", self.venv_load, self.command])

    @property
    def venv_load(self):
        if self._venv:
            with impr.path(kslurm.bin, "kpy-wrapper.sh") as path:
                return _LOAD_ENV.format(path=path, method="load", name=self._venv)
        return ""

    @property
    def venv_activate(self):
        if self._venv:
            with impr.path(kslurm.bin, "kpy-wrapper.sh") as path:
                return _LOAD_ENV.format(path=path, method="activate", name=self._venv)
        return ""

    ###
    # Job submission commands
    ###
    @property
    def run(self):
        if self.command:
            if os.environ.get("SLURM_JOB_ID") or os.environ.get("SLURM_JOBID"):
                return f"srun {self.slurm_args} {self.command}"
            command = self.venv_load + self.command
            return f"srun {self.slurm_args} bash -c {shlex.quote(command)}"
        command = (
            "srun --pty bash -c "
            + shlex.quote(f'bash --init-file <(echo "{self.venv_load}";)')
            if self.venv_load
            else ""
        )
        return f"salloc {self.slurm_args} {command}"

    @property
    def batch(self):
        if self.test:
            s = "cat"
        else:
            s = f"sbatch {self.slurm_args} --parsable {self.output}"
        if self.command:
            if "/" in self._command[0] and Path(self._command[0]).is_file():
                return f"{s} {self.command}"
            return f"echo {shlex.quote(self.script)} | {s}"
        else:
            raise ValidationError("No command given")

    @property
    def batch_test(self):
        s = f"sbatch {self.slurm_args} --test-only"
        if self.command:
            return f"echo {shlex.quote(self.script)} | {s}"
        else:
            raise ValidationError("No command given")
