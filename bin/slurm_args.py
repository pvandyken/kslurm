from pathlib import Path
import re
from typing import Iterable, List, Tuple, Union

class SlurmCommand:
    TIME = 'time'
    GPU = 'gpu'
    CPU = 'cpus'
    MEM = 'mem'
    JUPYTER = 'jupyter'
    ACCOUNT = 'account'
    COMMAND = 'command'
    DIRECTORY = 'directory'


    def __init__(self, args: List[str], time=180, cpu=1, gpu=False, jupyter=False, account='def-lpalaniy', mem=4000):
        labels = [label_arg(a) for a in args]
        slurm_args, self._command = delineate_command(args, labels)
        labelled = zip(slurm_args, labels)
        
        self._name = ""
        self.submit_script = [self.command]

        self.time = time
        self.cpu = cpu
        self.gpu = gpu
        self.jupyter = jupyter
        self.account = account
        self.mem = mem
        self.cwd  = Path.cwd()
        [self._add_arg(*a) for a in labelled]

    @property
    def slurm_args(self):
        s = f"--account={self.account} --time={self.time} --cpus-per-task={self.cpu} --mem={self.mem}"
        if self.gpu:
            s += " --gres=gpu:1"
        return s

    @property
    def command(self):
        return ' '.join(self._command)

    @property
    def command_list(self):
        return self._command

    @property
    def name(self):
        if not self._name:
            return self._command[0]
        else:
            return self._name
    
    @name.setter
    def name(self, name):
        self._name = name
        
    @property
    def interactive(self):
        s = f"salloc {self.slurm_args}"
        if self.command:
            s += f" {self.command}"
        return s

    @property
    def batch(self):
        s = f"sbatch {self.slurm_args} --job-name={self.name} --parsable --output=\"snakemake-%j.out\""
        if self.command:
            return f"echo '{self.submit_script}' | {s}"
        else:
            raise Exception("No command given")

    @property
    def submit_script(self):
        return self._submit_script

    @submit_script.setter
    def submit_script(self, command):
        self._submit_script = '\n'.join(['#!/bin/bash'] + command)

    def _add_arg(self, arg: str, label: str):
        if label == self.TIME:
            self.time = self._to_minutes(arg)
        elif label == self.GPU:
            self.gpu = True
        elif label == self.CPU:
            self.cpu = arg
        elif label == self.MEM:
            self.mem = self._to_mb(arg)
        elif label == self.JUPYTER:
            self.jupyter=True
        elif label == self.DIRECTORY:
            self.cwd = Path(arg).resolve()
        else:
            raise Exception("Unlabelled slurm argument")
        
    def _to_minutes(self, time):
        if '-' in time:
            days, hhmm = time.split('-')
            hours, min = hhmm.split(':')
        else:
            days = 0
            hours, min = time.split(':')
        return int(min) + int(hours)*60 + int(days)*60*24

    def _to_mb(self, mem):
        num = int(re.match(r'^[0-9]+', mem).group())
        if 'G' in mem:
            return num * 1000
        else:
            return num

def delineate_command(args: List[str], labels: List[str]):
    if SlurmCommand.COMMAND in labels:
        i = labels.index(SlurmCommand.COMMAND)
        return args[0:i], args[i:]
    else:
        return args, []

def label_arg(arg):
    if re.match(r'^([0-9]{1,2}-)?[0-9]{1,2}:[0-9]{2}$', arg):
        return SlurmCommand.TIME
    elif arg == "gpu":
        return SlurmCommand.GPU
    elif re.match(r'^[0-9]+$', arg):
        return SlurmCommand.CPU
    elif re.match(r'^[0-9]+[MG]B?$', arg):
        return SlurmCommand.MEM
    elif arg == "jupyter":
        return SlurmCommand.JUPYTER
    elif Path(arg).exists() and Path(arg).is_dir():
        return SlurmCommand.DIRECTORY
    else:
        return SlurmCommand.COMMAND