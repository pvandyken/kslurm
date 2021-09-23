from __future__ import absolute_import

import functools as ft
import json
import os
import re
import site
import sys
from contextlib import closing
from pathlib import Path
from typing import cast
from urllib.request import Request, urlopen

from kslurm.models import VERSION_REGEX


def data_dir(home_dir_var: str) -> Path:
    """Get directory to store app data and virtual env

    Returns the data directory for the app to be installed. It first checks if the
    python executable is inside the venv to be upgraded. Then, it checks the home_dir
    environment variable is set. It then checks the XDG_DATA_HOME environment var, then,
    if everything else is empty, returns the default path.

    Args:
        home_dir_var (str): Name of environment variable used to store the home dir path

    Returns:
        Path: Path of the home directory
    """

    dir = (Path(sys.executable) / "../../..").resolve()
    # Dir should have VERSION file
    if (dir / "VERSION").exists():
        return dir

    # If not, check if they have their HOME_DIR set
    if os.getenv(home_dir_var):
        return Path(os.getenv(home_dir_var)).expanduser()  # type: ignore

    # If still nothing, we'll just install at the usual place
    path = os.getenv("XDG_DATA_HOME", Path.home() / ".local/share")
    path = Path(path) / "kutils"

    return path


def bin_dir(home_dir_var: str) -> Path:
    """Get path of directory holding executable files.

    Returns the directory containing the user's local executable files. If the user
    has the HOME_DIR environment variable set, it will return the bin dir within that
    folder. The user will be responsible for ensuring that folder is on the PATH.
    Otherwise, it returns the default getuserbase() bin dir (.local/bin on linux)

    Args:
        home_dir_var (str): Name of environment variable containing HOMEDIR

    Returns:
        Path: Path to folder containing local executable files
    """
    if os.getenv(home_dir_var):
        return Path(os.getenv(home_dir_var), "bin").expanduser()  # type: ignore

    user_base = site.getuserbase()

    bin_dir = os.path.join(user_base, "bin")

    return Path(bin_dir)


def get(url: str):
    """Make an HTTP request and read the response.

    Args:
        url (str): URL to request

    Returns:
        str: Response from the http request read
    """
    request = Request(url, headers={"User-Agent": "Python kslurm"})

    with closing(urlopen(request)) as r:
        return r.read()


def get_version(
    requested_version: str,
    preview: bool,
    force: bool,
    data_dir: Path,
    metadata_url: str,
):
    version_regex = re.compile(VERSION_REGEX)
    current_version = None
    if data_dir.joinpath("VERSION").exists():
        current_version = data_dir.joinpath("VERSION").read_text().strip()

    metadata = json.loads(get(metadata_url).decode())

    def _compare_versions(x: str, y: str):
        mx = version_regex.match(x)
        my = version_regex.match(y)

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
    releases = sorted(metadata["releases"].keys(), key=ft.cmp_to_key(_compare_versions))

    if requested_version and requested_version not in releases:
        print(f"Version {requested_version} does not exist.")

        return None

    version = requested_version
    if not version:
        for release in reversed(releases):
            m = version_regex.match(release)
            if m and m.group(5) and not preview:
                continue

            version = release

            break
    assert isinstance(version, str)
    if current_version == version and not force:
        print(f"The latest version ({version}) is already installed.")

        return None

    return cast(str, version)
