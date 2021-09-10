from cluster_utils.args.arg_types import ShapeArg
from cluster_utils.slurm.slurm_args.args import ArgList
import os
from typing import Generic, List, TypeVar
import cluster_utils.args as arglib
from cluster_utils.exceptions import CommandLineError, TemplateError, ValidationError
from . import job_templates as templates
from . import helpers

T = TypeVar("T", bound=ArgList)


class SlurmCommand(Generic[T]):
    def __init__(self, args: List[str], model: T):
        self._name = ""
        self._output = ""

        

        try:
            parsed = arglib.parse_args(args, model)
        except CommandLineError as err:
            print(err.msg)
            if isinstance(err.src_err, TemplateError):
                print("Choose from the following list of templates:\n")
                templates.list_templates()
            exit()

        if parsed.list_job_templates.value:
            templates.list_templates()
            exit()

        # set_template returns templated values only if a template is passed
        # if we pass a blank string, the models are returned unchanged
        template = parsed.job_template.values[0] if parsed.job_template.value else ""
        template_vals = templates.set_template(
            template, mem=model.mem, cpu=model.cpu, time=model.time
        )

        self.time = template_vals.time
        self.cpu = template_vals.cpu
        self.mem = template_vals.mem

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

        self.command_script = [self.command]

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
    def run(self):
        s = f"salloc {self.slurm_args}"
        if self.command:
            s += f" {self.command}"
        return s

    @property
    def alloc(self):
        if self.command:
            return f"echo '{self.command}' | srun {self.slurm_args}"
        else:
            return self.run

    @property
    def batch(self):
        if self.test:
            s = "cat"
        else:
            s = f"sbatch {self.slurm_args} --job-name={self.name} --parsable {self.output}"
        if self.command:
            return f"echo '{self.command_script}' | {s}"
        else:
            raise ValidationError("No command given")

    @property
    def command_script(self):
        return self._submit_script

    @command_script.setter
    def command_script(self, command: List[str]):
        self._submit_script = "\n".join(["#!/bin/bash"] + command)

    @property
    def output(self):
        return self._output

    @output.setter
    def output(self, output: str):
        self._output = f'--output="{output}"'

    