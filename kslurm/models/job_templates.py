from __future__ import absolute_import, annotations

import functools as ft
import importlib.resources as impr
import itertools as it
import json
from typing import Dict, cast

import attr
from tabulate import tabulate
from typing_extensions import TypedDict

import kslurm.models.formatters as formatters


class Templates(TypedDict):
    cpus: str
    mem: str
    time: str


@attr.s(auto_attribs=True)
class TemplateArgs:
    mem: int
    cpu: int
    time: int


@ft.cache
def templates() -> Dict[str, Templates]:
    with impr.open_text("kslurm.data", "slurm_job_templates.json") as stream:
        data = json.load(stream)
    cast(Dict[str, Templates], data)
    return data


def set_template(template: str, mem: int, cpu: int, time: int):
    if template:
        if template not in templates():
            raise Exception(f"{template} is not a valid template")

        return TemplateArgs(
            mem=int(templates()[template]["mem"]),
            cpu=int(templates()[template]["cpus"]),
            time=formatters.time(templates()[template]["time"]),
        )
    else:
        return TemplateArgs(mem=mem, cpu=cpu, time=time)


def list_templates():
    labelled_values = list(templates().values())
    headers = ["name"] + list(labelled_values[0].keys())
    values = [list(value.values()) for value in labelled_values]
    entries = list(zip(templates().keys(), values))
    table = [list(it.chain([entry[0]], entry[1])) for entry in entries]
    print(tabulate(table, headers=headers, tablefmt="presto"))
