from __future__ import absolute_import

import os
from typing import Generic, List, TypeVar

import kslurm.args as arglib
import kslurm.models.job_templates as templates
import kslurm.slurm.helpers as helpers
from kslurm.args import ShapeArg
from kslurm.exceptions import TemplateError, ValidationError
from kslurm.models import SlurmModel

T = TypeVar("T", bound=SlurmModel)


class SlurmCommand(Generic[T]):
    def __init__(self, args: List[str], model: T):
        self._name = ""
        self._output = ""

        try:
            parsed = arglib.parse_args(args, model)
        except TemplateError as err:
            print(err.msg)
            print("Choose from the following list of templates:\n")
            templates.list_templates()
            exit()

        if parsed.list_job_templates.value and not parsed.help.value:
            templates.list_templates()
            exit()

        # set_template returns templated values only if a template is passed
        # if we pass a blank string, the models are returned unchanged
        template = parsed.job_template.values[0] if parsed.job_template.value else ""
        template_vals = templates.set_template(
            template, mem=model.mem, cpu=model.cpu, time=model.time
        )

        # Start by setting these three with model/template
        self.time = template_vals.time
        self.cpu = template_vals.cpu
        self.mem = template_vals.mem

        # Then update if values were specifically supplied on the command line
        if parsed.time.updated:
            self.time = parsed.time
        if parsed.cpu.updated:
            self.cpu = parsed.cpu
        if parsed.mem.updated:
            self.mem = parsed.mem

        self.gpu = bool(parsed.gpu.value)
        self.x11 = bool(parsed.x11.value)
        self.account = parsed.account
        self.cwd = parsed.directory
        self.test = bool(parsed.test.value)
        self.job_template = parsed.job_template
        self._command = parsed.tail.values
        self.help = bool(parsed.help.value)

        os.chdir(self.cwd.value)  # type: ignore

        self.script = [self.command]

        self.args = parsed

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
