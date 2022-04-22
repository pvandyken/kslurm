from __future__ import absolute_import

import hashlib
import importlib.resources as impr
import os
import re
import shutil
import subprocess as sp
import tarfile
import tempfile
import textwrap
import venv
from pathlib import Path
from typing import Any, Union

import attr
from virtualenv.create import pyenv_cfg  # type: ignore

from kslurm.appconfig import get_config
from kslurm.args.arg_types import FlagArg, PositionalArg, ShapeArg, SubCommand, TailArg
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


def _print_block(text: str):
    print(textwrap.dedent(text))


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

    index = KpyIndex(slurm_tmpdir)
    name = args.name.value

    venv_cache = Path(pipdir, "venv_archives")
    venvs_re = [re.search(r"(.+)\.tar\.gz$", str(f.name)) for f in venv_cache.iterdir()]
    venvs = [r.group(1) for r in venvs_re if r]

    if not name or name not in venvs:
        print("Valid venvs:\n\t" + "\n\t".join(venvs))
        return

    if name in index:
        print(
            f"An environment called '{name}' already exists. You can load '{name}' "
            "under a new name using --as:\n"
            f"\tkpy load {name} --as <name>\n"
            f"You can also activate the existing '{name}' using\n"
            f"\tkpy activate {name}"
        )
        return

    # pyload_venv_dir = slurm_tmpdir / "__virtual_environments__"
    # if (pyload_venv_dir / name).exists():
    #     shell = Shell.get()
    #     shell.activate(pyload_venv_dir / name)

    (slurm_tmpdir / "tmp").mkdir(parents=True, exist_ok=True)
    venv_dir = Path(tempfile.mkdtemp(prefix="kslurm-venv-", dir=slurm_tmpdir / "tmp"))
    print(f"Unpacking venv {name}")
    with tarfile.open(Path(venv_cache, name).with_suffix(".tar.gz"), "r") as tar:
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
    cfg.update({"prompt": name, "state_hash": get_hash(pip_freeze(venv_dir))})
    cfg.write()

    index[name] = str(venv_dir)
    index.write()
    shell = Shell.get()
    shell.activate(venv_dir)


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
    if "SLURM_TMPDIR" in os.environ:
        index = KpyIndex(Path(os.environ["SLURM_TMPDIR"]))
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
        try:
            sp.run(["command", "-v", "module"]).check_returncode()
        except sp.CalledProcessError:
            print("'module' command not present. Unable to load custom python versions")
            return
        sp.run(["module", "load", f"python/{args.version.value}"])

    slurm_tmp = os.environ.get("SLURM_TMPDIR")
    if slurm_tmp:
        index = KpyIndex(Path(slurm_tmp))
        name = args.name.value if args.name.value else _get_unique_name(index, "venv")
        if args.name.value in index:
            print(
                f"An environment called '{name}' already exists. You can activate "
                f"the existing '{name}' using\n"
                "\tkpy activate {name}"
            )
            return

        venv_dir = tempfile.mkdtemp(prefix="kslurm-venv-", dir=Path(slurm_tmp, "tmp"))
    else:
        index = None
        name = args.name.value if args.name.value else "venv"
        venv_dir = tempfile.mkdtemp(prefix="kslurm-")

    venv.create(venv_dir, symlinks=True, with_pip=True, prompt=name)
    sp.run(
        [os.path.join(venv_dir, "bin", "python"), "-m", "pip", "install", "--upgrade", "pip"]
    )
    if index is not None:
        index[name] = str(venv_dir)
        index.write()

    shell = Shell.get()
    shell.activate(Path(venv_dir))


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
