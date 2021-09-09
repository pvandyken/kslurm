from cluster_utils.slurm.slurm_args.args import ArgList
import os
from typing import Generic, List, TypeVar
import cluster_utils.args as arglib
from .job_templates import templates
from .slurm_args import formatters

T = TypeVar("T", bound=ArgList)

class SlurmCommand(Generic[T]):
    def __init__(self,
                 args: List[str],
                 arg_list: T):
        self._name = ""
        self._output = ""

        parsed = arglib.parse_args(
            args, arg_list)

        self.time = parsed.time
        self.cpu = parsed.cpu
        self.gpu = bool(parsed.gpu.value)
        self.jupyter = parsed.jupyter
        self.account = parsed.account
        self.mem = parsed.mem
        self.cwd = parsed.directory
        self.test = bool(parsed.test.value)
        self.job_template = parsed.job_template
        self._command = parsed.tail

        

        os.chdir(self.cwd.value)

        self.submit_script = [self.command]

        self.args = parsed

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
            raise Exception("No command given")

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
        self.mem = ArgList.mem.set_value(
            templates[template]["mem"]
        )
        self.cpu = ArgList().cpu.set_value(
            templates[template]["cpus"]
        )
        self.time = ArgList().time.set_value(
            formatters.time(templates[template]["time"])
        )
