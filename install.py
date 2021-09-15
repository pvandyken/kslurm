from typing import Optional, Tuple
from venv import EnvBuilder
from pathlib import Path
from venv import EnvBuilder
import os
import subprocess
import site
import shutil
import argparse
import sys

SHELL = os.getenv("SHELL", "")

ENTRYPOINTS = [
    "kbatch",
    "krun"
]

PRE_MESSAGE = """# Welcome to {software}!
This will download and install the latest version of {software},
a dependency and package manager for Python.
It will add the following commands to {software}'s bin directory:

{entrypoints}

These will be located at:

{software_home_bin}

You can uninstall at any time by executing this script with the --uninstall option,
and these changes will be reverted.
"""

POST_MESSAGE = """{software} is installed now. Great!
You can test that everything is set up by executing:
`{test_command}`
"""

POST_MESSAGE_NOT_IN_PATH = """{software} is installed now. Great!
To get started you need {software}'s bin directory ({software_home_bin}) in your `PATH`
environment variable.

{configure_message}

Alternatively, you can call {software} scripts explicitly. For instance, call
{software_executable_name} with `{software_executable}`.
You can test that everything is set up by executing:
`{test_command}`
"""

POST_MESSAGE_CONFIGURE_UNIX = """
Add `export PATH="{software_home_bin}:$PATH"` to your shell configuration file.
"""

POST_MESSAGE_CONFIGURE_FISH = """
You can execute `set -U fish_user_paths {software_home_bin} $fish_user_paths`
"""

def display_post_message(bin_dir: Path) -> None:
    if SHELL == "fish":
        message, configuration = get_post_message_fish(bin_dir)
    else:
        message, configuration = get_post_message_unix(bin_dir)

    print(
    message.format(
        software="Cluster Utils",
        software_home_bin=bin_dir,
        software_executable_name=ENTRYPOINTS[0],
        software_executable=bin_dir.joinpath(ENTRYPOINTS[0]),
        configure_message=configuration.format(
            software_home_bin=bin_dir
        ),
        test_command="kbatch --help",
    )
)


def get_post_message_fish(bin_dir: Path) -> Tuple[str, str]:
    fish_user_paths = subprocess.check_output(
        ["fish", "-c", "echo $fish_user_paths"]
    ).decode("utf-8")

    message = POST_MESSAGE_NOT_IN_PATH
    if fish_user_paths and str(bin_dir) in fish_user_paths:
        message = POST_MESSAGE
    
    return message, POST_MESSAGE_CONFIGURE_FISH

    

def get_post_message_unix(bin_dir: Path) -> Tuple[str, str]:
    paths = os.getenv("PATH", "").split(":")

    message = POST_MESSAGE_NOT_IN_PATH
    if paths and str(bin_dir) in paths:
        message = POST_MESSAGE

    return message, POST_MESSAGE_CONFIGURE_UNIX


def display_pre_message(bin_dir: Path) -> None:
    kwargs = {
        "software": "Cluster Utils",
        "software_home_bin": bin_dir,
        "entrypoints": ", ".join(ENTRYPOINTS)
    }
    print(PRE_MESSAGE.format(**kwargs))

def string_to_bool(value: str) -> bool:
    value = value.lower()

    return value in {"true", "1", "y", "yes"}


def data_dir() -> Path:
    if os.getenv("POETRY_HOME"):
        return Path(os.getenv("CLUSTER_HOME")).expanduser() # type: ignore

    
    path = os.getenv("XDG_DATA_HOME", Path.home() / ".local/share")
    path = Path(path) / "kutils"

    return path

def bin_dir(version: Optional[str] = None) -> Path:
    if os.getenv("CLUSTER_HOME"):
        return Path(os.getenv("CLUSTER_HOME"), "bin").expanduser() # type: ignore

    user_base = site.getuserbase()

    bin_dir = os.path.join(user_base, "bin")

    return Path(bin_dir)

def check_os():
    if not (sys.platform == "linux" or sys.platform == "linux2"):
        print("Currently, only linux platforms are supported")
        return False
    else:
        return True

def install(data_dir: Path, bin_dir: Path):
    """
    Installs Software.
    """
    data_dir.mkdir(parents=True, exist_ok=True)
    env_path = make_env(data_dir)
    install_library(env_path)
    make_bin(bin_dir, data_dir)
    # self.install_poetry(version, env_path)
    # self.make_bin(version)

    # self._overwrite(
    #     "Installing {} ({}): {}".format(
    #         colorize("info", "Poetry"),
    #         colorize("b", version),
    #         colorize("success", "Done"),
    #     )
    # )

    # self._data_dir.joinpath("VERSION").write_text(version)

    return 0

def make_env(data_dir: Path) -> Path:
    print("Making virtual env")
    env_path = data_dir / "venv"
    EnvBuilder(with_pip=True, clear=True).create(str(env_path))
    return env_path

def install_library(env_path: Path) -> None:
    print("Installing")
    python = env_path.joinpath("bin/python")
    specification = "git+https://github.com/pvandyken/cluster_utils.git"

    subprocess.run(
        [str(python), "-m", "pip", "install", specification],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=True,
    )


def make_bin(bin_dir: Path, data_dir: Path) -> None:
    bin_dir.mkdir(parents=True, exist_ok=True)

    for script in ENTRYPOINTS:
        target_script = "venv/bin/" + script
        if bin_dir.joinpath(script).exists():
            bin_dir.joinpath(script).unlink()

        bin_dir.joinpath(script).symlink_to(
            data_dir.joinpath(target_script)
        )

def uninstall(data_dir: Path, bin_dir: Path) -> int:
    if not data_dir.exists():
        print(
            "Cluster-utils is not currently installed."
        )
        return 1
    print("Removing Cluster-utils")

    shutil.rmtree(str(data_dir))
    for script in ENTRYPOINTS:
        if bin_dir.joinpath(script).is_symlink():
            bin_dir.joinpath(script).unlink()

    return 0

def main():
    if not check_os():
        return 1
    parser = argparse.ArgumentParser(
        description="Installs the latest (or given) version of poetry"
    )
    parser.add_argument(
        "--uninstall",
        help="uninstall poetry",
        dest="uninstall",
        action="store_true",
        default=False,
    )

    args = parser.parse_args()

    

    if args.uninstall or string_to_bool(os.getenv("POETRY_UNINSTALL", "0")):
        return uninstall(data_dir(), bin_dir())

    display_pre_message(bin_dir())
    try:
        install(data_dir(), bin_dir())
    except subprocess.CalledProcessError as e:
        print(
            f"\nAn error has occurred: {e}\n{e.stderr.decode()}"
        )
        return e.returncode
    display_post_message(bin_dir())
    return 0

if __name__ == "__main__":
    sys.exit(main())