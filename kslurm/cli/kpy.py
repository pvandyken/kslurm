from __future__ import absolute_import

import hashlib
import importlib.resources as impr
import os
import re
import shutil
import subprocess as sp
import sys
import tarfile
import tempfile
from pathlib import Path
from typing import Any, Literal, Optional, Union, cast, overload

import attr
from virtualenv.create import pyenv_cfg  # type: ignore

from kslurm.args import Subcommand, flag, keyword, positional, shape, subcommand
from kslurm.args.command import CommandError, command
from kslurm.args.types import WrappedCommand
from kslurm.shell import Shell
from kslurm.venv import KpyIndex, MissingPipdirError, VenvCache


def _get_hash(item: Union[str, bytes]):
    if isinstance(item, str):
        item = item.encode()
    return hashlib.md5(item).hexdigest()


def _pip_freeze(venv_dir: Path):
    return sp.run(
        [venv_dir / "bin" / "python", "-m", "pip", "freeze"], capture_output=True
    ).stdout


def _get_unique_name(index: KpyIndex, stem: str = "venv", i: int = 0) -> str:
    if i == 0:
        candidate = stem
    else:
        candidate = f"{stem}{i}"
    if candidate in index:
        return _get_unique_name(index, stem, i + 1)
    return candidate


class MissingSlurmTmpdirError(CommandError):
    pass


@overload
def _get_slurm_tmpdir(allow_missing: Literal[True] = ...) -> Optional[Path]:
    ...


@overload
def _get_slurm_tmpdir(allow_missing: Literal[False] = ...) -> Path:
    ...


def _get_slurm_tmpdir(allow_missing: bool = True):
    if not os.environ.get("SLURM_TMPDIR"):
        if not allow_missing:
            raise MissingSlurmTmpdirError(
                "This command can only be used in a compute node. Use `krun` to start "
                "an interactive session"
            )
        return
    return Path(os.environ["SLURM_TMPDIR"])


@command
def _bash():
    """Echo script for inclusion in .bashrc

    e.g.
        kpy bash >> $HOME/.bashrc
    """
    with impr.path("kslurm.bin", "bash.sh") as path:
        print(f"\nsource {path.resolve()}")


@command(typer=True)
def _load(
    name: str = positional(default="", help="Test help"),
    new_name: list[str] = keyword(match=["--as"]),
    script: list[str] = keyword(match=["--script"]),
):
    """Load a saved python venv

    Run without name to list available venvs for loading
    """
    slurm_tmp = _get_slurm_tmpdir()
    if slurm_tmp:
        index = KpyIndex(slurm_tmp)

        label = new_name[0] if new_name else name
        if label in index:
            print(
                f"An environment called '{label}' already exists. You can load "
                f"'{name}' under a different name using --as:\n"
                f"\tkpy load {label} --as <name>\n"
                f"You can also activate the existing '{label}' using\n"
                f"\tkpy activate {label}"
            )
            return 1
        venv_dir = Path(tempfile.mkdtemp(prefix="kslurm-venv-", dir=slurm_tmp / "tmp"))
    else:
        index = None
        label = name
        venv_dir = Path(tempfile.mkdtemp(prefix="kslurm-"))

    venv_cache = VenvCache()

    if not name or name not in venv_cache:
        print("Valid venvs:\n" + str(venv_cache))
        return

    print(f"Unpacking venv '{name}'", end="")
    if label != name:
        print(f" as '{label}'")
    else:
        print()
    with tarfile.open(venv_cache[name], "r") as tar:
        tar.extractall(venv_dir)

    print("Updating paths")
    with (venv_dir / "bin" / "activate").open("r") as f:
        lines = f.read().splitlines()
        # \x22 and \x27 are " and ' char
        subbed = [
            re.sub(
                r"(?<=^VIRTUAL_ENV=([\x22\x27])).*(?=\1$)",
                str(venv_dir),
                line,
            )
            for line in lines
        ]
    with (venv_dir / "bin" / "activate").open("w") as f:
        f.write("\n".join(subbed))

    for root, _, files in os.walk(venv_dir / "bin"):
        for file in files:
            path = Path(root, file)
            if path.is_symlink() or not os.access(path, os.X_OK):
                continue
            with path.open("r") as f:
                lines = f.read().splitlines()
                subbed = [
                    re.sub(
                        r"(?<=^#!)/.*$",
                        str(venv_dir / "bin" / "python"),
                        line,
                    )
                    for line in lines
                ]
            with path.open("w") as f:
                f.write("\n".join(subbed))

    cfg: Any = pyenv_cfg.PyEnvCfg.from_folder(venv_dir)  # type: ignore
    cfg.update({"prompt": label, "state_hash": _get_hash(_pip_freeze(venv_dir))})
    cfg.write()

    if index is not None:
        index[label] = str(venv_dir)
        index.write()

    shell = Shell.get()
    if script:
        with Path(script[0]).open("w") as f:
            f.write(shell.source(venv_dir))
        return 2
    shell.activate(venv_dir)


@command(typer=True)
def _save(name: str = positional(), force: bool = flag(match=["--force", "-f"])):
    """Save current venv"""
    if not os.environ.get("VIRTUAL_ENV"):
        print(
            "No active virtual env detected. Please activate one, or ensure "
            "$VIRTUAL_ENV is being set correctly"
        )
    venv_cache = VenvCache()

    delete = False
    if name in venv_cache:
        if force:
            delete = True
        else:
            print(f"{name} already exists. Run with -f to force overwrite")
            return

    dest = venv_cache.get_path(name)

    _, tmp = tempfile.mkstemp(prefix="kslurm-", suffix="tar.gz")

    venv_dir = Path(os.environ["VIRTUAL_ENV"])
    cfg: Any = pyenv_cfg.PyEnvCfg.from_folder(venv_dir)  # type: ignore
    cfg.update(
        {
            "prompt": name,
            "state_hash": _get_hash(_pip_freeze(venv_dir)),
        }
    )
    cfg.write()
    with tarfile.open(tmp, mode="w:gz") as tar:
        tar.add(venv_dir, arcname="")

    if delete:
        os.remove(dest)
    slurm_tmp = _get_slurm_tmpdir()
    if slurm_tmp:
        index = KpyIndex(slurm_tmp)
        index[name] = str(venv_dir)
        index.write()
    shutil.move(tmp, dest)


@command(typer=True)
def _create(
    name: str = positional("", help="Name of the new venv"),
    version: str = shape(
        default="",
        match=lambda s: bool(re.match(r"^[23]\.\d{1,2}$", s)),
        syntax="(2|3).x",
        examples=["2.7", "3.8"],
        help="Python version to use in new venv. An appropriate executable must be on "
        "the $PATH (e.g. 3.7 -> python3.7",
    ),
    script: list[str] = keyword(match=["--script"]),
):
    """Create a new venv

    If no name provided, a placeholder name will be generated
    """
    if version:
        ver = ["-p", version]
    else:
        try:
            data = sp.run(
                "eval $($LMOD_CMD bash list python)", shell=True, capture_output=True
            )
            if match := re.search(r"(?<=python\/)\d\.\d{1,2}", data.stdout.decode()):
                ver = ["-p", match[0]]
            else:
                ver = []
        except RuntimeError:
            ver = []

    slurm_tmp = _get_slurm_tmpdir()
    if slurm_tmp:
        index = KpyIndex(slurm_tmp)
        name = name if name else _get_unique_name(index, "venv")
        if name in index:
            print(
                f"An environment called '{name}' already exists. You can activate "
                f"the existing '{name}' using\n"
                "\tkpy activate {name}"
            )
            return 1

        venv_dir = tempfile.mkdtemp(prefix="kslurm-venv-", dir=slurm_tmp / "tmp")
        no_download = ["--no-download"]
        no_index = ["--no-index"]
    else:
        index = None
        name = name if name else "venv"
        venv_dir = tempfile.mkdtemp(prefix="kslurm-")
        no_download = []
        no_index = []

    try:
        sp.run(
            [
                sys.executable,
                "-m",
                "virtualenv",
                venv_dir,
                "--symlinks",
                "--prompt",
                name,
                *ver,
                *no_download,
            ],
        )
        sp.run(
            [
                os.path.join(venv_dir, "bin", "python"),
                "-m",
                "pip",
                "install",
                "--upgrade",
                "pip",
                *no_index,
            ],
        )
    except RuntimeError as err:
        print(err.args[0])
        return 1
    if index is not None:
        index[name] = str(venv_dir)
        index.write()

    shell = Shell.get()
    if script:
        with Path(script[0]).open("w") as f:
            f.write(shell.source(Path(venv_dir)))
        return 2
    shell.activate(Path(venv_dir))


@command(typer=True)
def _activate(name: str = positional(""), script: list[str] = keyword(["--script"])):
    """Activate a venv already created or loaded

    Only works on compute nodes. Use kpy create or kpy load --as on a login node
    """
    slurm_tmp = _get_slurm_tmpdir(False)
    index = KpyIndex(slurm_tmp)
    if not name:
        print(str(index))
        return

    if name not in index:
        print(
            f"An environment with the name '{name}' has not yet been initialized. ",
            end="",
        )
        try:
            venv_cache = VenvCache()
            if name in venv_cache:
                print(
                    f"The saved environment called '{name}' can be loaded using\n"
                    f"\tkpy load {name}\n"
                )
        except MissingPipdirError:
            pass
        print(f"A new environment can be created using\n\tkpy create {name}")
        print(f"Currently initialized environments:\n{index}")
        return 1

    shell = Shell.get()
    if script:
        with Path(script[0]).open("w") as f:
            f.write(shell.source(Path(index[name])))
        return 2
    shell.activate(Path(index[name]))


@command
def _list():
    """List all saved venvs.

    To list initialized venvs (either created or loaded), run `kpy activate` without any
    arguments
    """
    venv_cache = VenvCache()
    print(str(venv_cache))
    return


@command
def _refresh():
    try:
        dir = Path(os.environ["VIRTUAL_ENV"])
        cfg: Any = pyenv_cfg.PyEnvCfg.from_folder(dir)  # type: ignore
        state_hash = cfg["state_hash"]
    except KeyError:
        return

    try:
        hsh = _get_hash(_pip_freeze(dir))
        if hsh != state_hash and cfg["prompt"][0] != "*":
            cfg["prompt"] = "*" + cfg["prompt"]
        elif hsh == state_hash and cfg["prompt"][0] == "*":
            cfg["prompt"] = cfg["prompt"][1:]
        cfg.write()
    except KeyError:
        return


def _kpy_wrapper(argv: list[str] = sys.argv):
    with impr.path("kslurm.bin", "kpy-wrapper.sh") as path:
        print(path)


@command(typer=True)
def _rm(name: str = positional("")):
    try:
        venv_cache = VenvCache()
    except MissingPipdirError as err:
        print(err.msg)
        return 1

    if not name:
        print("Valid venvs:\n" + str(venv_cache))

    if name not in venv_cache:
        print(f"{name} is not a valid venv. Currently saved venvs are:\n{venv_cache}")
        return 1

    os.remove(venv_cache[name])
    return


@attr.frozen
class _KpyModel:
    command: Subcommand = subcommand(
        commands={
            "load": _load,
            "save": _save,
            "bash": _bash,
            "create": _create,
            "activate": _activate,
            "list": _list,
            "rm": _rm,
            "_refresh": _refresh,
            "_kpy_wrapper": cast(WrappedCommand, _kpy_wrapper),
        },
    )


@command
def kpy(cmd_name: str, args: _KpyModel, tail: list[str]):
    """Set of commands for interacting with python virtual envs"""
    name, func = args.command
    entry = f"{cmd_name} {name}"
    return func([entry, *tail])


if __name__ == "__main__":
    kpy(["kpy", "--help"])
