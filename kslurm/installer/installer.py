from __future__ import absolute_import

import subprocess
from pathlib import Path
from typing import List
from venv import EnvBuilder

from kslurm.args import parse_args
from kslurm.installer.utils import bin_dir, data_dir, get_current_version, get_version
from kslurm.installer.version import FlexVersion
from kslurm.models.update import UpdateModel

METADATA_URL = "https://pypi.org/pypi/kslurm/json"


def install(args: List[str], name: str, home_dir: str, entrypoints: List[str] = []):
    parsed = parse_args(args, UpdateModel())
    data = data_dir(home_dir)
    bin = bin_dir(home_dir)
    print("Checking for Updates")
    version = get_version(parsed.version.value, False, METADATA_URL)
    if version is None:
        return 1
    try:
        if FlexVersion.parse(version) == get_current_version(data):
            print(f"Already up to date! (v{version})")
            return 0
    except ValueError:
        # Can't compare versions, so we update
        pass

    specification = f"{name}=={version}"

    return run_installation(version, specification, data, bin, True, entrypoints)


def run_installation(
    version: str,
    specification: str,
    data_dir: Path,
    bin_dir: Path,
    update: bool = False,
    entrypoints: List[str] = [],
):
    """
    Installs Software.
    """
    try:
        data_dir.mkdir(parents=True, exist_ok=True)
        bin_dir.mkdir(parents=True, exist_ok=True)
        env_path = _make_env(data_dir, update)
        _install_library(specification, env_path)
        if entrypoints:
            _make_bin(bin_dir, data_dir, entrypoints)

        data_dir.joinpath("VERSION").write_text(version)

        return 0
    except subprocess.CalledProcessError as e:
        print(f"\nAn error has occurred: {e}\n{e.stderr}")
        return e.returncode


def _make_env(data_dir: Path, update: bool = False) -> Path:
    """Return path to virtualenv, creating one in the process if necessary

    Creates a virtualenv in the directory specified: `datadir/venv/...`. If `update` is
    `True` and the `data_dir` already contains a virtualenv, the path to the virtualenv
    will be returned with no creation

    Args:
        data_dir (Path): Directory in which the venv should be created (or looked for)
        update (bool, optional): If true and a virtualenv exists at `data_dir/venv`, no
            venv will be created. Defaults to False.

    Returns:
        Path: Path of the virtualenv
    """
    env_path = data_dir / "venv"
    if update and _is_venv(env_path):
        return env_path
    print("Making virtual env")
    EnvBuilder(with_pip=True, clear=True).create(str(env_path))
    return env_path


def _is_venv(venv: Path) -> bool:
    python = venv / "bin/python"
    pip = venv / "bin/pip"
    # If pip and python exist, that's enough to install something,
    # so we assume it's a venv
    if python.exists() and pip.exists():
        return True
    return False


def _install_library(specification: str, env_path: Path) -> None:
    """Pip installs the specification using the Python found in the env_path

    Args:
        specification (str): Valid label for pip install (e.g. pkg==x.x.x, git=url,
            path)
        env_path (Path): Path to virtualenv where package should be installed"""
    print("Installing")
    python = env_path.joinpath("bin/python")

    subprocess.run(
        [str(python), "-m", "pip", "install", specification],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=True,
    )


def _make_bin(bin_dir: Path, data_dir: Path, entrypoints: List[str]) -> None:
    bin_dir.mkdir(parents=True, exist_ok=True)

    for script in entrypoints:
        target_script = "venv/bin/" + script
        if bin_dir.joinpath(script).is_symlink():
            bin_dir.joinpath(script).unlink()

        bin_dir.joinpath(script).symlink_to(data_dir.joinpath(target_script))
