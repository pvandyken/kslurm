from typing import Dict, cast
from typing_extensions import TypedDict
import itertools as it
from tabulate import tabulate
import attr, json
from pathlib import Path
import functools as ft
from cluster_utils.args import ShapeArg


class Templates(TypedDict):
    cpus: str
    mem: str
    time: str


@attr.s(auto_attribs=True)
class TemplateArgs:
    mem: ShapeArg[int]
    cpu: ShapeArg[int]
    time: ShapeArg[int]


@ft.lru_cache
def templates() -> Dict[str, Templates]:
    file = Path(f"{__file__}/../../data/slurm_job_templates.json").resolve()

    if not file.exists():
        raise FileNotFoundError(
            "Could not locate slurm_job_templates.json " f"at {file.resolve()}"
        )
    with file.open() as data_stream:
        data = json.load(data_stream)
    cast(Dict[str, Templates], data)
    return data


def set_template(
    template: str, mem: ShapeArg[int], cpu: ShapeArg[int], time: ShapeArg[int]
):
    if template:
        if not template in templates():
            raise Exception(f"{template} is not a valid template")

        return TemplateArgs(
            mem=mem.set_value(templates()[template]["mem"]),
            cpu=cpu.set_value(templates()[template]["cpus"]),
            time=time.set_value(templates()[template]["time"]),
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