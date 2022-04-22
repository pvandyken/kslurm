from __future__ import absolute_import

import importlib.resources as impr
import os
import re
import tarfile
from pathlib import Path

import attr

from kslurm.appconfig import get_config
from kslurm.args.arg_types import PositionalArg, SubCommand, TailArg
from kslurm.args.command import command
from kslurm.shell import Shell


@command
def _bash():
    with impr.path("kslurm.bin", "bash.sh") as path:
        print(f"\nsource {path.resolve()}")


@attr.frozen
class _LoadModel:
    name: PositionalArg[str] = PositionalArg(value="")


@command
def _load(args: _LoadModel):
    if not os.environ.get("SLURM_TMPDIR"):
        print(
            "This command can only be used in a compute node. Use `krun` to start an "
            "interactive session"
        )
        return
    slurm_tmpdir = Path(os.environ["SLURM_TMPDIR"])
    pipdir = get_config("pipdir")
    if not pipdir:
        print(
            "pipdir not set. Please set pipdir using `kslurm config pipdir "
            "<directory>`, typically to a project-space or permanent storage directory"
        )
        return
    venv_cache = Path(pipdir, "venv_archives")
    venvs_re = [re.search(r"(.+)\.tar\.gz$", str(f.name)) for f in venv_cache.iterdir()]
    venvs = [r.group(1) for r in venvs_re if r]

    name = args.name.value
    if not name or name not in venvs:
        print("Valid venvs:\n\t" + "\n\t".join(venvs))
        return

    pyload_venv_dir = slurm_tmpdir / "__virtual_environments__"
    if (pyload_venv_dir / name).exists():
        shell = Shell.get()
        shell.activate(pyload_venv_dir / name)

    tmp = tempfile.mkdtemp(prefix="kslurm-", dir=slurm_tmpdir / "tmp")
    print(f"Unpacking venv {name}")
    with tarfile.open(Path(venv_cache, name).with_suffix(".tar.gz"), "r") as tar:
        tar.extractall(tmp)

    print("Updating paths")
    with (pyload_venv_dir / name / "bin" / "activate").open("r") as f:
        lines = f.read().splitlines()
        # \x22 and \x27 are " and ' char
        subbed = [
            re.sub(
                r"(?<=^VIRTUAL_ENV=([\x22\x27])).*(?=\1$)",
                str(pyload_venv_dir / name),
                line,
            )
            for line in lines
        ]
    with (pyload_venv_dir / name / "bin" / "activate").open("w") as f:
        f.write("\n".join(subbed))

    for root, _, files in os.walk(pyload_venv_dir / name / "bin"):
        for file in files:
            path = Path(root, file)
            if path.is_symlink() or not os.access(path, os.X_OK):
                continue
            with path.open("r") as f:
                lines = f.read().splitlines()
                subbed = [
                    re.sub(
                        r"(?<=^#!)/.*$",
                        str(pyload_venv_dir / name / "bin" / "python"),
                        line,
                    )
                    for line in lines
                ]
            with path.open("w") as f:
                f.write("\n".join(subbed))

    pyload_venv_dir.mkdir(parents=True)
    shutil.move(tmp, pyload_venv_dir / name)
    shell = Shell.get()
    shell.activate(pyload_venv_dir / name)


@attr.frozen
class KpyModel:
    command: SubCommand = SubCommand(
        commands={
            "load": _load,
            "save": _bash,
            "bash": _bash,
        },
    )

    tail: TailArg = TailArg("Args")


@command
def kpy(args: KpyModel) -> None:
    command = args.command.value
    tail = args.tail
    name = f"kslurm {args.command.raw_value}"
    command([name, *tail.values])
