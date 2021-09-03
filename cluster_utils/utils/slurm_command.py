from pathlib import Path
import os
from typing import Iterable, List, Tuple, cast

import toolz as tz
import functools as fc

import cluster_utils.args as arglib

class SlurmCommand:
    def __init__(self,
                 args: List[str], 
                 time: int = 180, 
                 cpu: int = 1, 
                 gpu: bool = False, 
                 jupyter: bool = False, 
                 account: str = 'def-lpalaniy', 
                 mem: int = 4000,
                 job_template: str=""):
        self._name = ""
        self._output = ""
        

        self.time = time
        self.cpu = cpu
        self.gpu = gpu
        self.jupyter = jupyter
        self.account = account
        self.mem = mem
        self.cwd  = Path.cwd()
        self.test = False
        self.job_template = job_template

        labelled = [classify_arg(a) for a in args]
        positional, keywords = extract_keywords(labelled)
        slurm_args, command = delineate_command(positional)
        self._command = command
        [self._parse_shapearg(l) for l in slurm_args]
        os.chdir(self.cwd)

        self.submit_script = [self.command]

    @property
    def slurm_args(self):
        s = f"--account={self.account} --time={self.time} --cpus-per-task={self.cpu} --mem={self.mem}"
        if self.gpu:
            s += " --gres=gpu:1"
        return s

    @property
    def command(self):
        return ' '.join(map(str, self._command))

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

    def _parse_shapearg(self, s_arg: arglib.Arg):
        assert isinstance(s_arg, arglib.ShapeArg)
        label = s_arg.id
        arg = s_arg.arg
        
        if label == arglib.TIME:
            self.time = arg
        elif label == arglib.GPU:
            self.gpu = True
        elif label == arglib.CPU:
            self.cpu = arg
        elif label == arglib.MEM:
            self.mem = arg
        elif label == arglib.JUPYTER:
            self.jupyter=True
        elif label == arglib.DIRECTORY:
            self.cwd = Path(arg).resolve()
        elif label == arglib.TEST:
            self.test = True
        else:
            raise Exception("Unlabelled slurm argument")
        
    # def _parse_keywordarg(self, k_arg: List[arglib.Arg]):
    #     keyword, entries = k_arg
    #     assert isinstance(keyword.argtype, arglib.KewordArg)
    #     label = keyword.argtype.id
    #     if label == arglib.JOB_TEMPLATE:
    #         pass


def classify_arg(arg: str):
    for argtype in arglib.arg_list:
        if argtype.match(arg):
            return argtype(arg)
    return cast(arglib.Arg, arglib.command_arg(arg))


def extract_keywords(args: List[arglib.Arg]) -> Tuple[Iterable[arglib.Arg], Iterable[List[arglib.Arg]]]:
    keyword_group_size = [
        get_keyword_group_size(arg) for arg in args
    ]

    # We add 1 to size if size is not 0 when indexing 
    # to account for the keyword arg itself
    keyword_groups = [
        args[i : i+incr_if_positive(size)] for i, size in enumerate(keyword_group_size)
    ]
    # The reduction of get_non_keywords returns the tuple:
    #   (group_size, argument_list)
    # so we index to get argument_list
    non_keywords = fc.reduce(get_non_keywords, args, (0, cast(List[arglib.Arg], [])))[1]

    return (
        non_keywords,
        filter(None, keyword_groups)
    )

def get_keyword_group_size(arg: arglib.Arg):
    if isinstance(arg, arglib.KeywordArg):
        return arg.num
    else:
        return 0

def get_non_keywords(accumulant: Tuple[int, Iterable[arglib.Arg]], arg: arglib.Arg) -> Tuple[int, Iterable[arglib.Arg]]:
    curr_keyword_group, running_list = accumulant
    new_keyword_group_size = get_keyword_group_size(arg)

    if curr_keyword_group > 0 and new_keyword_group_size > 0:
        raise Exception("Can't start a new group when another group is running")

    # If we have a new keyword group, we increase its size by 
    # one to account for the keyword argument itself
    group_size = incr_if_positive(new_keyword_group_size) + curr_keyword_group


    # If group_size is above zero, we are in a keyword group,
    # so we don't want to take the current arg
    if group_size:
        return group_size - 1, running_list
    else:
        return 0, tz.concat([running_list, [arg]])


def delineate_command(args: Iterable[arglib.Arg]) -> Tuple[List[arglib.Arg], List[arglib.Arg]]:
    arg_list = list(args)
    label_ids = [arg.id for arg in arg_list]
    if arglib.COMMAND in label_ids:
        i = label_ids.index(arglib.COMMAND)
        return arg_list[0:i], arg_list[i:]
    else:
        return list(args), []


def incr_if_positive(num: int):
    if num > 0:
        return num + 1
    else:
        return num
