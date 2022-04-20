from __future__ import absolute_import

import os
import sys
from typing import List, Union

import kslurm.appconfig as appconfig
import kslurm.models.job_templates as templates
import kslurm.slurm.helpers as helpers
from kslurm.args import ShapeArg
from kslurm.exceptions import TemplateError, ValidationError
from kslurm.models import SlurmModel


class SlurmCommand:
    def __init__(self, args: Union[SlurmModel, TemplateError]):
        self._name = ""
        self._output = ""

        if isinstance(args, TemplateError):
            print(args.msg)
            print("Choose from the following list of templates:\n")
            templates.list_templates()
            exit()

        if args.list_job_templates.value and not args.help.value:
            templates.list_templates()
            exit()

        # set_template returns templated values only if a template is passed
        # if we pass a blank string, the models are returned unchanged
        template = args.job_template.values[0] if args.job_template.value else ""
        template_vals = templates.set_template(
            template, mem=args.mem, cpu=args.cpu, time=args.time
        )

        # Start by setting these three with model/template
        self.time = template_vals.time
        self.cpu = template_vals.cpu
        self.mem = template_vals.mem

        # Then update if values were specifically supplied on the command line
        if args.time.updated:
            self.time = args.time
        if args.cpu.updated:
            self.cpu = args.cpu
        if args.mem.updated:
            self.mem = args.mem

        self.gpu = bool(args.gpu.value)
        self.x11 = bool(args.x11.value)
        if not args.account.values:
            self.account = appconfig.get_config("account")
            if not self.account:
                print(
                    "Account must either be specified using --account, or provided in "
                    "config. A default account can be added to config by running "
                    "kslurm config account <account_name>"
                )
                sys.exit(1)
        else:
            self.account = str(args.account)
        self.cwd = args.directory
        self.test = bool(args.test.value)
        self.job_template = args.job_template
        self._command = args.tail.values
        self.help = bool(args.help.value)

        os.chdir(self.cwd.value)  # type: ignore

        self.script = [self.command]

        self.args = args

    ###
    # Job Paramaters
    ###
    @property
    def time(self):
        return helpers.slurm_time_format(self._time.value)  # type: ignore

    @time.setter
    def time(self, time: ShapeArg[int]):
        self._time = time

    @property
    def name(self):
        if not self._name:
            return self._command[0]
        else:
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
        return s

    @property
    def command(self):
        return " ".join(self._command)

    @command.setter
    def command(self, commands: List[str]):
        self._command = commands

    @property
    def script(self):
        return self._script

    @script.setter
    def script(self, command: List[str]):
        self._script = "\n".join(["#!/bin/bash"] + command)

    ###
    # Job submission commands
    ###
    @property
    def run(self):
        if self.command:
            return f"echo '{self.command}' | srun {self.slurm_args} bash"
        else:
            return f"salloc {self.slurm_args}"

    @property
    def batch(self):
        if self.test:
            s = "cat"
        else:
            s = (
                f"sbatch {self.slurm_args} --job-name={self.name} "
                f"--parsable {self.output}"
            )
        if self.command:
            return f"echo '{self.script}' | {s}"
        else:
            raise ValidationError("No command given")
