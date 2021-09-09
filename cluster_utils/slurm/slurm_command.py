from cluster_utils.args.arg_types import ShapeArg
from cluster_utils.slurm.slurm_args.args import ArgList
import os
from typing import Generic, List, TypeVar
import cluster_utils.args as arglib
from cluster_utils.exceptions import CommandLineError
from .job_templates import templates
from . import helpers

T = TypeVar("T", bound=ArgList)

class SlurmCommand(Generic[T]):
    def __init__(self,
                 args: List[str],
                 model: T):
        self._name = ""
        self._output = ""

        self.time = model.time
        self.cpu = model.cpu
        self.mem = model.mem

        parsed = arglib.parse_args(
            args, model)

            
        if parsed.job_template.value:
            self._set_template(parsed.job_template.values[0])

        if parsed.time.updated:
            self.time = parsed.time
        if parsed.cpu.updated:
            self.cpu = parsed.cpu
        if parsed.mem.updated:
            self.mem = parsed.mem
        self.gpu = bool(parsed.gpu.value)
        self.jupyter = parsed.jupyter
        self.account = parsed.account
        self.cwd = parsed.directory
        self.test = bool(parsed.test.value)
        self.job_template = parsed.job_template
        self._command = parsed.tail


        os.chdir(self.cwd.value)

        self.submit_script = [self.command]

        self.args = parsed

    @property
    def time(self):
        return helpers.slurm_time_format(self._time.value)


    @time.setter
    def time(self, time: ShapeArg[int]):
        self._time = time

    @property
    def slurm_args(self):
        s = f"--account={self.account} --time={self.time} --cpus-per-task={self.cpu} --mem={self.mem}"
        if self.gpu:
            s += " --gres=gpu:1"
        return s

    @property
    def command(self):
        return str(self._command)

    @property
    def name(self):
        if not self._name:
            return self._command.values[0]
        else:
            return self._name

    @name.setter
    def name(self, name: str):
        self._name = name

    @property
    def interactive(self):
        s = f"salloc {self.slurm_args}"
        if self.command:
            s += f" {self.command}"
        return s

    @property
    def batch(self):
        if self.test:
            s = "cat"
        else:
            s = f"sbatch {self.slurm_args} --job-name={self.name} --parsable {self.output}"
        if self.command:
            return f"echo '{self.submit_script}' | {s}"
        else:
            raise CommandLineError("No command given")

    @property
    def submit_script(self):
        return self._submit_script

    @submit_script.setter
    def submit_script(self, command: List[str]):
        self._submit_script = '\n'.join(['#!/bin/bash'] + command)

    @property
    def output(self):
        return self._output

    @output.setter
    def output(self, output: str):
        self._output = f"--output=\"{output}\""

    def _set_template(self, template: str):
        if not template in templates:
            raise Exception(f"{template} is not a valid template")
        self.mem = ArgList().mem.set_value(
            templates[template]["mem"]
        )
        self.cpu = ArgList().cpu.set_value(
            templates[template]["cpus"]
        )
        self.time = ArgList().time.set_value(
            templates[template]["time"]
        )

    def _list_templates(self):

        pass