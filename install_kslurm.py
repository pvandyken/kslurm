# The following was adapted from install_poetry.py from Poetry,
# published under the MIT License:

# Copyright (c) 2018 Sébastien Eustace

# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:

# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

# The entire library can be found at https://github.com/python-poetry/poetry


from typing import Optional, Tuple, cast, List, Iterable
from venv import EnvBuilder
from pathlib import Path
from venv import EnvBuilder
import os
import subprocess
import site
import shutil
import argparse
import sys
import re
import json
import functools as ft
from urllib.request import Request, urlopen
from contextlib import closing
from io import UnsupportedOperation

SHELL = os.getenv("SHELL", "")

NAME = "kslurm"
HOME_DIR = "KSLURM_HOME"

ENTRYPOINTS = [
    "kbatch",
    "krun",
    "kjupyter"
]

FOREGROUND_COLORS = {
    "black": 30,
    "red": 31,
    "green": 32,
    "yellow": 33,
    "blue": 34,
    "magenta": 35,
    "cyan": 36,
    "white": 37,
}

BACKGROUND_COLORS = {
    "black": 40,
    "red": 41,
    "green": 42,
    "yellow": 43,
    "blue": 44,
    "magenta": 45,
    "cyan": 46,
    "white": 47,
}

OPTIONS = {"bold": 1, "underscore": 4, "blink": 5, "reverse": 7, "conceal": 8}


def style(fg: Optional[str], bg: Optional[str], options: Optional[Iterable[str]]):
    codes = cast(List[int], [])

    if fg:
        codes.append(FOREGROUND_COLORS[fg])

    if bg:
        codes.append(BACKGROUND_COLORS[bg])

    if options:
        for option in options:
            codes.append(OPTIONS[option])

    return "\033[{}m".format(";".join(map(str, codes)))


STYLES = {
    "info": style("cyan", None, None),
    "comment": style("yellow", None, None),
    "success": style("green", None, None),
    "error": style("red", None, None),
    "warning": style("yellow", None, None),
    "b": style(None, None, ("bold",)),
}


def is_decorated():
    

    if not hasattr(sys.stdout, "fileno"):
        return False

    try:
        return os.isatty(sys.stdout.fileno())
    except UnsupportedOperation:
        return False


def is_interactive():
    if not hasattr(sys.stdin, "fileno"):
        return False

    try:
        return os.isatty(sys.stdin.fileno())
    except UnsupportedOperation:
        return False


def colorize(style: str, text: str):
    if not is_decorated():
        return text

    return "{}{}\033[0m".format(STYLES[style], text)

PRE_MESSAGE = """# Welcome to {software}!
This will download and install the latest version of {software},
providing helper scripts and wrappers for running commands on
SLURM compute clusters.
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

METADATA_URL = "https://pypi.org/pypi/kslurm/json"
VERSION_REGEX = re.compile(
    r"v?(\d+)(?:\.(\d+))?(?:\.(\d+))?(?:\.(\d+))?"
    "("
    "[._-]?"
    r"(?:(stable|beta|b|rc|RC|alpha|a|patch|pl|p)((?:[.-]?\d+)*)?)?"
    "([.-]?dev)?"
    ")?"
    r"(?:\+[^\s]+)?"
)

def display_post_message(bin_dir: Path) -> None:
    if SHELL == "fish":
        message, configuration = get_post_message_fish(bin_dir)
    else:
        message, configuration = get_post_message_unix(bin_dir)

    print(
    message.format(
        software=NAME,
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
        "software": NAME,
        "software_home_bin": bin_dir,
        "entrypoints": ", ".join(ENTRYPOINTS)
    }
    print(PRE_MESSAGE.format(**kwargs))

def string_to_bool(value: str) -> bool:
    value = value.lower()

    return value in {"true", "1", "y", "yes"}


def get(url: str):
    request = Request(url, headers={"User-Agent": "Python kslurm"})

    with closing(urlopen(request)) as r:
        return r.read()


def data_dir() -> Path:
    if os.getenv(HOME_DIR):
        return Path(os.getenv(HOME_DIR)).expanduser() # type: ignore

    
    path = os.getenv("XDG_DATA_HOME", Path.home() / ".local/share")
    path = Path(path) / "kutils"

    return path

def bin_dir(version: Optional[str] = None) -> Path:
    if os.getenv(HOME_DIR):
        return Path(os.getenv(HOME_DIR), "bin").expanduser() # type: ignore

    user_base = site.getuserbase()

    bin_dir = os.path.join(user_base, "bin")

    return Path(bin_dir)

def check_os():
    if not (sys.platform == "linux" or sys.platform == "linux2"):
        print("Currently, only linux platforms are supported")
        return False
    else:
        return True

def check_python():
    major, minor = sys.version_info[0:2]
    if major == 3 and minor > 6:
        return True
    else:
        print("Please run script with Python version 3.7 or greater")
        print(f"Current python version: {sys.version}")

def install(version: str, specification: str, data_dir: Path, bin_dir: Path):
    """
    Installs Software.
    """
    data_dir.mkdir(parents=True, exist_ok=True)
    bin_dir.mkdir(parents=True, exist_ok=True)
    env_path = make_env(data_dir)
    install_library(specification, env_path)
    make_bin(bin_dir, data_dir)

    data_dir.joinpath("VERSION").write_text(version)

    return 0

def make_env(data_dir: Path) -> Path:
    print("Making virtual env")
    env_path = data_dir / "venv"
    EnvBuilder(with_pip=True, clear=True).create(str(env_path))
    return env_path

def install_library(specification: str, env_path: Path) -> None:
    print("Installing")
    python = env_path.joinpath("bin/python")

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
        if bin_dir.joinpath(script).is_symlink():
            bin_dir.joinpath(script).unlink()

        bin_dir.joinpath(script).symlink_to(
            data_dir.joinpath(target_script)
        )

def uninstall(data_dir: Path, bin_dir: Path) -> int:
    if not data_dir.exists():
        print(
            f"{NAME} is not currently installed."
        )
        return 1
    print(f"Removing {NAME}")

    shutil.rmtree(str(data_dir))
    for script in ENTRYPOINTS:
        if bin_dir.joinpath(script).is_symlink():
            bin_dir.joinpath(script).unlink()

    return 0

def get_version(requested_version: Optional[str], preview: bool, force: bool, data_dir: Path):
    current_version = None
    if data_dir.joinpath("VERSION").exists():
        current_version = data_dir.joinpath("VERSION").read_text().strip()

    print(colorize("info", "Retrieving Poetry metadata"))

    metadata = json.loads(get(METADATA_URL).decode())

    def _compare_versions(x:str, y:str):
        mx = VERSION_REGEX.match(x)
        my = VERSION_REGEX.match(y)

        if mx and my:
            vx = tuple(int(p) for p in mx.groups()[:3]) + (mx.group(5),)
            vy = tuple(int(p) for p in my.groups()[:3]) + (my.group(5),)

            if vx < vy:
                return -1
            elif vx > vy:
                return 1

            return 0
        else:
            raise Exception("Could not match version information")

    print("")
    releases = sorted(
        metadata["releases"].keys(), key=ft.cmp_to_key(_compare_versions)
    )

    if requested_version and requested_version not in releases:
        print(
            colorize("error", f"Version {requested_version} does not exist.")
        )

        return None

    version = requested_version
    if not version:
        for release in reversed(releases):
            m = VERSION_REGEX.match(release)
            if m and m.group(5) and not preview:
                continue

            version = release

            break
    assert isinstance(version, str)
    if current_version == version and not force:
        print(
            "The latest version ({}) is already installed.".format(
                colorize("b", version)
            )
        )

        return None

    return cast(str, version)

def main():
    if not check_os() or not check_python():
        return 1
    parser = argparse.ArgumentParser(
        description=f"Installs the latest (or given) version of {NAME}"
    )
    parser.add_argument(
        "--uninstall",
        help=f"uninstall {NAME}",
        dest="uninstall",
        action="store_true",
        default=False,
    )

    parser.add_argument(
        "-f",
        "--force",
        help="install on top of existing version",
        dest="force",
        action="store_true",
        default=False,
    )

    parser.add_argument(
        "--path",
        dest="path",
        action="store",
        help=(
            "Install from a given path (file or directory) instead of "
            "fetching the latest version of Poetry available online."
        ),
    )

    parser.add_argument(
        "-p",
        "--preview",
        help="install preview version",
        dest="preview",
        action="store_true",
        default=False,
    )

    parser.add_argument(
        "--git",
        dest="git",
        action="store",
        help=(
            "Install from a git repository instead of fetching the latest version "
            "of Poetry available online."
        ),
    )

    parser.add_argument("--version", help="install named version", dest="version")

    args = parser.parse_args()

    

    if args.uninstall or string_to_bool(os.getenv("KSLURM_UNINSTALL", "0")):
        return uninstall(data_dir(), bin_dir())

    if args.git:
        version = args.git
        specification = f"git+{args.git}"
    elif args.path:
        version = cast(str, args.path)
        specification = version
    else:
        version = get_version(args.version, args.preview, args.force, data_dir())
        if version:
            specification = f"kslurm=={version}"

    
    if version is None:
        return 0

    display_pre_message(bin_dir())
    try:
        install(version, specification, data_dir(), bin_dir()) # type: ignore
    except subprocess.CalledProcessError as e:
        print(
            f"\nAn error has occurred: {e}\n{e.stderr}"
        )
        return e.returncode
    display_post_message(bin_dir())
    return 0

if __name__ == "__main__":
    sys.exit(main())