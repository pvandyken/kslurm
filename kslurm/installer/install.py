import subprocess
from typing import List
from venv import EnvBuilder
from pathlib import Path

def install(
        version: str, 
        specification: str, 
        data_dir: Path, 
        bin_dir: Path, 
        update: bool=False, 
        entrypoints: List[str] = []
    ):
    """
    Installs Software.
    """
    try:
        data_dir.mkdir(parents=True, exist_ok=True)
        bin_dir.mkdir(parents=True, exist_ok=True)
        env_path = make_env(data_dir, update)
        install_library(specification, env_path)
        if entrypoints:
            make_bin(bin_dir, data_dir, entrypoints)

        data_dir.joinpath("VERSION").write_text(version)

        return 0
    except subprocess.CalledProcessError as e:
        print(
            f"\nAn error has occurred: {e}\n{e.stderr}"
        )
        return e.returncode

def make_env(data_dir: Path, update: bool = False) -> Path:
    env_path = data_dir / "venv"
    if update and is_venv(env_path):
        return env_path
    print("Making virtual env")
    EnvBuilder(with_pip=True, clear=True).create(str(env_path))
    return env_path

def is_venv(venv: Path) -> bool:
    python = venv / "bin/python"
    pip = venv / "bin/pip"
    # If pip and python exist, that's enough to install something,
    # so we assume it's a venv
    if python.exists() and pip.exists():
        return True
    return False

def install_library(specification: str, env_path: Path) -> None:
    print("Installing")
    python = env_path.joinpath("bin/python")

    subprocess.run(
        [str(python), "-m", "pip", "install", specification],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=True,
    )

def make_bin(bin_dir: Path, data_dir: Path, entrypoints: List[str]) -> None:
    bin_dir.mkdir(parents=True, exist_ok=True)

    for script in entrypoints:
        target_script = "venv/bin/" + script
        if bin_dir.joinpath(script).is_symlink():
            bin_dir.joinpath(script).unlink()

        bin_dir.joinpath(script).symlink_to(
            data_dir.joinpath(target_script)
        )