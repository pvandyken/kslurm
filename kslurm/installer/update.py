from typing import List

from kslurm.args import parse_args
from kslurm.installer.install import install
from kslurm.installer.utils import bin_dir, data_dir, get_version
from kslurm.models import UpdateModel

METADATA_URL = "https://pypi.org/pypi/kslurm/json"
NAME = "kslurm"
HOME_DIR = "KSLURM_HOME"
ENTRYPOINTS = ["kbatch", "krun", "kjupyter", "kslurm"]


def update(args: List[str]):
    parsed = parse_args(args, UpdateModel())
    data = data_dir(HOME_DIR)
    bin = bin_dir(HOME_DIR)
    print("Checking for Updates")
    version = get_version(parsed.version.value, False, False, data, METADATA_URL)
    if version is None:
        return 1
    specification = f"kslurm=={version}"

    return install(version, specification, data, bin, True, ENTRYPOINTS)


if __name__ == "__main__":
    update([])
