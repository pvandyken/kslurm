from __future__ import absolute_import

import json
import os
import site
import sys
from contextlib import closing
from pathlib import Path
from typing import Optional
from urllib.request import Request, urlopen

from kslurm.installer.version import FlexVersion


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
    requested_version: Optional[str],
    preview: bool,
    metadata_url: str,
):
    """Retrieves version information and returns a valid version for installation.

    If no specific version is requested, it will return the latest version. Otherwise,
    it will check to make sure the requested version is valid.

    Args:
        requested_version (str or None): Specific version to request. If None, request
            latest version.
        preview (bool): Set to True to allow preview or development versions
        metadata_url (str): url to pipy repository metadata

    Returns:
        Optional[str]: Valid version for installation. Returns None if requested
            version does not exist
    """

    metadata = json.loads(get(metadata_url).decode())

    releases = sorted([FlexVersion.parse(k) for k in metadata["releases"].keys()])

    if requested_version:
        version = FlexVersion.parse(requested_version)
        for release in releases:
            if version == release:
                return release.raw_value
        print(f"Version {requested_version} does not exist.")
        return None
    else:
        for release in reversed(releases):
            if release.prerelease and not preview:
                continue
            return release.raw_value


def get_current_version(datadir: Path) -> Optional[str]:
    """Retrieves current version from the app data directory, if it exists

    Args:
        datadir (Path): Path of the data directory

    Returns:
        Optional[str]: The current version, otherwise None
    """
    if datadir.joinpath("VERSION").exists():
        return datadir.joinpath("VERSION").read_text().strip()
    return None
