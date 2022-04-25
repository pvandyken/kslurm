from __future__ import absolute_import

import sys

from kslurm.style.console import console


def check_python_version():
    if sys.version_info.major < 3 or sys.version_info.minor < 9:
        console.print(
            "[WARNING] You are using an outdated version of python. The latest "
            "versions of kslurm will only install on python 3.9 or higher.",
            style="yellow",
        )
