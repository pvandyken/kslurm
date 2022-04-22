from __future__ import absolute_import

import importlib.resources as impr
import os
import re
import shutil
import subprocess as sp
import tarfile
import tempfile
import venv
from pathlib import Path
from typing import Any

import attr
from virtualenv.create import pyenv_cfg  # type: ignore

from kslurm.appconfig import get_config
from kslurm.args.arg_types import FlagArg, PositionalArg, ShapeArg, SubCommand, TailArg
from kslurm.args.command import command
from kslurm.shell import Shell


@command
def _bash():
    """Echo script for inclusion in .bashrc

    e.g.
        kpy bash >> $HOME/.bashrc
    """
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

    (slurm_tmpdir / "tmp").mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix="kslurm-", dir=slurm_tmpdir / "tmp"))
    print(f"Unpacking venv {name}")
    with tarfile.open(Path(venv_cache, name).with_suffix(".tar.gz"), "r") as tar:
        tar.extractall(tmp)

    print("Updating paths")
    with (tmp / "bin" / "activate").open("r") as f:
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
    with (tmp / "bin" / "activate").open("w") as f:
        f.write("\n".join(subbed))

    for root, _, files in os.walk(tmp / "bin"):
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

    cfg: Any = pyenv_cfg.PyEnvCfg.from_folder(tmp)  # type: ignore
    cfg.update({"prompt": name})
    cfg.write()

    pyload_venv_dir.mkdir(parents=True, exist_ok=True)
    shutil.move(str(tmp), pyload_venv_dir / name)
    shell = Shell.get()
    shell.activate(pyload_venv_dir / name)


@attr.frozen
class _SaveModel:
    name: PositionalArg[str] = PositionalArg()
    force: FlagArg = FlagArg(match=["--force", "-f"])


@command
def _save(args: _SaveModel):
    if not os.environ.get("VIRTUAL_ENV"):
        print(
            "No active virtual env detected. Please activate one, or ensure "
            "$VIRTUAL_ENV is being set correctly"
        )
    pipdir = get_config("pipdir")
    if not pipdir:
        print(
            "pipdir not set. Please set pipdir using `kslurm config pipdir "
            "<directory>`, typically to a project-space or permanent storage directory"
        )
        return

    venv_cache = Path(pipdir, "venv_archives")
    dest = (venv_cache / args.name.value).with_suffix(".tar.gz")

    delete = False
    if dest.exists():
        if args.force.value:
            delete = True
        else:
            print(f"{dest} already exists. Run with -f to force overwrite")
            return

    _, tmp = tempfile.mkstemp(prefix="kslurm-", suffix="tar.gz")
    with tarfile.open(tmp, mode="w:gz") as tar:
        tar.add(os.environ["VIRTUAL_ENV"], arcname="")

    if delete:
        os.remove(dest)
    shutil.move(tmp, dest)


@attr.frozen
class _CreateModel:
    name: PositionalArg[str] = PositionalArg("")
    version: ShapeArg[str] = ShapeArg(
        value="", match=lambda s: bool(re.match(r"^[23]\.\d{1,2}$", s))
    )


@command
def _create(args: _CreateModel):
    if os.environ.get("SLURM_TMPDIR"):
        dir = tempfile.mkdtemp(
            prefix="kslurm", dir=Path(os.environ["SLURM_TMPDIR"], "tmp")
        )
    else:
        dir = tempfile.mkdtemp(prefix="kslurm-")

    if args.version.value:
        try:
            sp.run(["command", "-v", "module"]).check_returncode()
        except sp.CalledProcessError:
            print("'module' command not present. Unable to load custom python versions")
            return
        sp.run(["module", "load", f"python/{args.version.value}"])

    name = args.name.value if args.name.value else "venv"
    venv.create(dir, symlinks=True, with_pip=True, prompt=name)
    sp.run(
        [os.path.join(dir, "bin", "python"), "-m", "pip", "install", "--upgrade", "pip"]
    )
    shell = Shell.get()
    shell.activate(Path(dir))


@attr.frozen
class KpyModel:
    command: SubCommand = SubCommand(
        commands={
            "load": _load,
            "save": _save,
            "bash": _bash,
            "create": _create,
        },
    )

    tail: TailArg = TailArg("Args")


@command
def kpy(args: KpyModel) -> None:
    command = args.command.value
    tail = args.tail
    name = f"kslurm {args.command.raw_value}"
    command([name, *tail.values])
