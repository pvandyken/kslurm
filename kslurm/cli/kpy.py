from __future__ import absolute_import

import hashlib
import importlib.resources as impr
import os
import re
import shutil
import subprocess as sp
import tarfile
import tempfile
from collections import UserDict
from pathlib import Path
from typing import Any, Literal, Optional, Union, overload

import attr
import virtualenv  # type: ignore
from virtualenv.create import pyenv_cfg  # type: ignore

from kslurm.appconfig import get_config
from kslurm.args.arg_types import (
    FlagArg,
    KeywordArg,
    PositionalArg,
    ShapeArg,
    SubCommand,
    TailArg,
)
from kslurm.args.command import command
from kslurm.kpyindex import KpyIndex
from kslurm.shell import Shell


def get_hash(item: Union[str, bytes]):
    if isinstance(item, str):
        item = item.encode()
    return hashlib.md5(item).hexdigest()


def pip_freeze(venv_dir: Path):
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


class MissingPipdirError(Exception):
    def __init__(self, msg: str, *args: Any):
        super().__init__(msg, *args)
        self.msg = msg


class MissingSlurmTmpdirError(Exception):
    def __init__(self, msg: str, *args: Any):
        super().__init__(msg, *args)
        self.msg = msg


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


class VenvCache(UserDict[str, Path]):
    def __init__(self):
        pipdir = get_config("pipdir")
        if pipdir is None:
            raise MissingPipdirError(
                "pipdir not set. Please set pipdir using `kslurm config pipdir "
                "<directory>`, typically to a project-space or permanent storage "
                "directory"
            )
        self.venv_cache = Path(pipdir, "venv_archives")
        self.venv_cache.mkdir(exist_ok=True)
        venvs_re = [
            re.search(r"(.+)\.tar\.gz$", str(f.name)) for f in self.venv_cache.iterdir()
        ]
        venvs = [r.group(1) for r in venvs_re if r]
        self.data = {v: self._construct_path(v) for v in venvs}

    def get_path(self, name: str):
        try:
            return self.data[name]
        except KeyError:
            return self._construct_path(name)

    def _construct_path(self, name: str):
        return (self.venv_cache / name).with_suffix(".tar.gz")


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
    new_name: KeywordArg[str] = KeywordArg(match=["--as"])


@command
def _load(args: _LoadModel):
    slurm_tmp = _get_slurm_tmpdir()
    if slurm_tmp:
        index = KpyIndex(slurm_tmp)
        name = args.name.value

        label = args.new_name.values[0] if args.new_name.values else name
        if label in index:
            print(
                f"An environment called '{label}' already exists. You can load "
                f"'{name}' under a different name using --as:\n"
                f"\tkpy load {label} --as <name>\n"
                f"You can also activate the existing '{label}' using\n"
                f"\tkpy activate {label}"
            )
            return
        venv_dir = Path(tempfile.mkdtemp(prefix="kslurm-venv-", dir=slurm_tmp / "tmp"))
    else:
        index = None
        name = args.name.value
        label = name
        venv_dir = Path(tempfile.mkdtemp(prefix="kslurm-"))

    pipdir = get_config("pipdir")
    if not pipdir:
        print(
            "pipdir not set. Please set pipdir using `kslurm config pipdir "
            "<directory>`, typically to a project-space or permanent storage directory"
        )
        return

    name = args.name.value

    try:
        venv_cache = VenvCache()
    except MissingPipdirError as err:
        print(err.msg)
        return

    if not name or name not in venv_cache:
        print("Valid venvs:\n\t" + "\n\t".join(venv_cache))
        return

    # pyload_venv_dir = slurm_tmpdir / "__virtual_environments__"
    # if (pyload_venv_dir / name).exists():
    #     shell = Shell.get()
    #     shell.activate(pyload_venv_dir / name)

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
    cfg.update({"prompt": label, "state_hash": get_hash(pip_freeze(venv_dir))})
    cfg.write()

    if index is not None:
        index[label] = str(venv_dir)
        index.write()

    shell = Shell.get()
    if n := shell.activate(venv_dir):
        kpy(n)


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
    try:
        venv_cache = VenvCache()
    except MissingPipdirError as err:
        print(err.msg)
        return

    name = args.name.value
    delete = False
    if name in venv_cache:
        if args.force.value:
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
            "prompt": args.name.value,
            "state_hash": get_hash(pip_freeze(venv_dir)),
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
        index[args.name.value] = str(venv_dir)
        index.write()
    shutil.move(tmp, dest)


@attr.frozen
class _CreateModel:
    name: PositionalArg[str] = PositionalArg("")
    version: ShapeArg[str] = ShapeArg(
        value="", match=lambda s: bool(re.match(r"^[23]\.\d{1,2}$", s))
    )


@command
def _create(args: _CreateModel):
    if args.version.value:
        ver = ["-p", args.version.value]
    else:
        ver = []

    slurm_tmp = _get_slurm_tmpdir()
    if slurm_tmp:
        index = KpyIndex(slurm_tmp)
        name = args.name.value if args.name.value else _get_unique_name(index, "venv")
        if args.name.value in index:
            print(
                f"An environment called '{name}' already exists. You can activate "
                f"the existing '{name}' using\n"
                "\tkpy activate {name}"
            )
            return

        venv_dir = tempfile.mkdtemp(prefix="kslurm-venv-", dir=slurm_tmp / "tmp")
        no_download = ["--no-download"]
        no_index = ["--no-index"]
    else:
        index = None
        name = args.name.value if args.name.value else "venv"
        venv_dir = tempfile.mkdtemp(prefix="kslurm-")
        no_download = []
        no_index = []

    try:
        virtualenv.cli_run(  # type: ignore
            [venv_dir, "--symlinks", "--prompt", name, *ver, *no_download]
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
            ]
        )
    except RuntimeError as err:
        print(err.args[0])
        return
    if index is not None:
        index[name] = str(venv_dir)
        index.write()

    shell = Shell.get()
    n = shell.activate(Path(venv_dir))
    if n:
        kpy(n)


@attr.frozen
class ActivateModel:
    name: PositionalArg[str] = PositionalArg()


@command
def _activate(args: ActivateModel):
    try:
        slurm_tmp = _get_slurm_tmpdir(False)
    except MissingSlurmTmpdirError as err:
        print(err.msg)
        return

    index = KpyIndex(slurm_tmp)
    name = args.name.value
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
        return

    shell = Shell.get()
    n = shell.activate(Path(index[name]))
    if n:
        kpy(n)


@command
def _list():
    try:
        slurm_tmp = _get_slurm_tmpdir(False)
    except MissingSlurmTmpdirError as err:
        print(err.msg)
        return
    index = KpyIndex(slurm_tmp)
    print("\n".join(index))


@command
def _refresh():
    try:
        dir = Path(os.environ["VIRTUAL_ENV"])
        cfg: Any = pyenv_cfg.PyEnvCfg.from_folder(dir)  # type: ignore
        state_hash = cfg["state_hash"]
    except KeyError:
        return

    try:
        hsh = get_hash(pip_freeze(dir))
        if hsh != state_hash and cfg["prompt"][0] != "*":
            cfg["prompt"] = "*" + cfg["prompt"]
        elif hsh == state_hash and cfg["prompt"][0] == "*":
            cfg["prompt"] = cfg["prompt"][1:]
        cfg.write()
    except KeyError:
        return


@attr.frozen
class KpyModel:
    command: SubCommand = SubCommand(
        commands={
            "load": _load,
            "save": _save,
            "bash": _bash,
            "create": _create,
            "activate": _activate,
            "list": _list,
            "_refresh": _refresh,
        },
    )

    tail: TailArg = TailArg("Args")


@command
def kpy(args: KpyModel) -> None:
    command = args.command.value
    tail = args.tail
    name = f"kslurm {args.command.raw_value}"
    command([name, *tail.values])


if __name__ == "__main__":
    kpy(["kpy", "bash", "--help"])
