from __future__ import absolute_import

import importlib.resources as impr
import os
import re
import shutil
import subprocess as sp
import sys
import tarfile
import tempfile
from pathlib import Path
from typing import Literal, Optional, overload

import attr
from shellingham import ShellDetectionFailure

from kslurm.appconfig import InvalidPipdirError
from kslurm.args import Subcommand, choice, flag, keyword, positional, shape, subcommand
from kslurm.args.command import CommandError, command
from kslurm.args.help import SKIPHELP
from kslurm.models import validators
from kslurm.shell import Shell
from kslurm.venv import KpyIndex, PromptRefreshError, VenvCache, VenvPrompt, rebase_venv


def _get_unique_name(index: KpyIndex, stem: str = "venv", i: int = 0) -> str:
    if i == 0:
        candidate = stem
    else:
        candidate = f"{stem}{i}"
    if candidate in index:
        return _get_unique_name(index, stem, i + 1)
    return candidate


def _get_shell():
    try:
        return Shell.get()
    except ShellDetectionFailure as err:
        raise CommandError(err.args[0])


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


@command(inline=True)
def _load(
    name: str = positional(default=""),
    new_name: str = keyword(match=["--as"], format=validators.fs_name),
    script: str = keyword(match=["--script"], help=SKIPHELP),
):
    """Load a saved python venv

    Run without name to list available venvs for loading

    Attributes:
        name: Name of the venv to load. If not specified, list all available venvs
        new_name:
            Load the venv under a different name. Useful for loading the same venv twice
    """
    slurm_tmp = _get_slurm_tmpdir()
    if slurm_tmp:
        index = KpyIndex(slurm_tmp)

        label = new_name or name
        if label in index:
            raise CommandError(
                f"An environment called '{label}' already exists. You can load "
                f"'{name}' under a different name using --as:\n"
                f"\tkpy load {label} --as <name>\n"
                f"You can also activate the existing '{label}' using\n"
                f"\tkpy activate {label}"
            )
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
    rebase_venv(venv_dir)

    prompt = VenvPrompt(venv_dir)
    prompt.update_prompt(label)
    prompt.update_hash()
    prompt.save()

    if index is not None:
        index[label] = str(venv_dir)
        index.write()

    shell = _get_shell()
    if script:
        with Path(script).open("w") as f:
            f.write(shell.source(venv_dir))
        return 2
    shell.activate(venv_dir)


@command(inline=True)
def _export(
    mode: str = choice(["venv"], help="What sort of export to perform"),
    name: str = positional(),
    path: Path = keyword(["--path", "-p"], default=None),
):
    """Export a saved venv

    Saves to a path of choice. Currently "venv" is the only valid export mode. Exported
    venvs can only be safely activated by a bash shell.

    Attributes:
        name: Name of the venv to export
        path: Path for the export
    """
    venv_cache = VenvCache()

    if name not in venv_cache:
        raise CommandError("Valid venvs:\n" + str(venv_cache))

    if path.exists():
        raise CommandError(f"{path} already exists")

    print("exporting...")
    with tarfile.open(venv_cache[name], "r") as tar:
        tar.extractall(path)
    rebase_venv(path)

    print(
        "Export complete! Activate the venv by running\n\tsource "
        f"{path}/bin/activate"
    )


@command(inline=True)
def _save(
    name: str = positional(format=validators.fs_name),
    force: bool = flag(match=["--force", "-f"]),
):
    """Save current venv

    Attributes:
        name:
            Name to save venv under. If a venv of this name already exists, an error
            will be thrown, unless force is used
        force:
            Overwrite any existing venv with chosen name
    """
    if not os.environ.get("VIRTUAL_ENV"):
        raise CommandError(
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

    _, tmp = tempfile.mkstemp(prefix="kslurm-", suffix=".tar.gz")

    venv_dir = Path(os.environ["VIRTUAL_ENV"])
    prompt = VenvPrompt(venv_dir)
    prompt.update_prompt(name)
    prompt.update_hash()
    prompt.save()
    with tarfile.open(tmp, mode="w:gz") as tar:
        tar.add(venv_dir, arcname="")

    slurm_tmp = _get_slurm_tmpdir()
    if slurm_tmp:
        index = KpyIndex(slurm_tmp)
        index[name] = str(venv_dir)
        index.write()

    # Do a two stage move in case tmp and dest are on different file systems, which
    # could make the move take some time. This lets us delete the old dest at the last
    # possible second
    stage = dest.with_suffix(".tar.gz.tmp")
    shutil.move(tmp, stage)
    if delete:
        os.remove(dest)
    shutil.move(stage, dest)


@command(inline=True)
def _create(
    name: Optional[str] = positional(format=validators.fs_name),
    version: Optional[str] = shape(
        match=r"^[23]\.\d{1,2}$",
        examples=["2.7", "3.8"],
    ),
    script: str = keyword(match=["--script"], help=SKIPHELP),
):
    """Create a new venv

    If no name provided, a placeholder name will be generated

    Attributes:
        name: Name of the new venv

        version:
            Python version to use in new venv. An appropriate executable must be on the
            $PATH (e.g. 3.7 -> python3.7)

            @help.syntax (2|3).x
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
            raise CommandError(
                f"An environment called '{name}' already exists. You can activate "
                f"the existing '{name}' using\n"
                "\tkpy activate {name}"
            )

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
    prompt = VenvPrompt(Path(venv_dir))
    prompt.update_prompt(name)
    prompt.save()

    shell = _get_shell()
    if script:
        with Path(script).open("w") as f:
            f.write(shell.source(Path(venv_dir)))
        return 2
    shell.activate(Path(venv_dir))


@command(inline=True)
def _activate(
    name: Optional[str] = positional(),
    script: str = keyword(["--script"], help=SKIPHELP),
):
    """Activate a venv already created or loaded

    Only works on compute nodes. Use kpy create or kpy load --as on a login node

    Attributes:
        name: Name of the venv to activate. If not provided, list all loaded venvs
    """
    slurm_tmp = _get_slurm_tmpdir(False)
    index = KpyIndex(slurm_tmp)
    if not name:
        print(str(index))
        return

    if name not in index:
        err = [f"An environment with the name '{name}' has not yet been initialized. "]
        try:
            venv_cache = VenvCache()
            if name in venv_cache:
                err += [
                    f"The saved environment called '{name}' can be loaded using",
                    f"\tkpy load {name}\n",
                ]
        except InvalidPipdirError:
            pass
        err += [
            f"A new environment can be created using\n\tkpy create {name}\n",
            f"Currently initialized environments:\n{index}",
        ]
        raise CommandError("\n".join(err))

    shell = _get_shell()
    if script:
        with Path(script).open("w") as f:
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
    except KeyError:
        return
    prompt = VenvPrompt(dir)
    try:
        prompt.refresh()
        print(prompt.name)
    except PromptRefreshError:
        return


def _kpy_wrapper(argv: list[str] = sys.argv):
    with impr.path("kslurm.bin", "kpy-wrapper.sh") as path:
        print(path)
    return 0


@command(inline=True)
def _rm(name: Optional[str] = positional()):
    """Delete a venv
    Args:
        name (Optional[str], optional):
            Name of the venv to delete

    """
    venv_cache = VenvCache()

    if not name:
        raise CommandError("Valid venvs:\n" + str(venv_cache))

    if name not in venv_cache:
        raise CommandError(
            f"{name} is not a valid venv. Currently saved venvs are:\n{venv_cache}"
        )

    os.remove(venv_cache[name])


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
            "export": _export,
            "_refresh": _refresh,
            "_kpy_wrapper": _kpy_wrapper,
        },
    )


@command
def kpy(cmd_name: str, args: _KpyModel, tail: list[str]):
    """Set of commands for interacting with python virtual envs"""
    name, func = args.command
    entry = f"{cmd_name} {name}"
    return func([entry, *tail])


if __name__ == "__main__":
    kpy.cli(["kpy", "foo"])
