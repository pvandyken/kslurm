from __future__ import absolute_import

import hashlib
import subprocess as sp
from typing import TypeVar, Union

T = TypeVar("T")


def get_hash(item: Union[str, bytes], method: str = "md5"):
    if isinstance(item, str):
        item = item.encode()
    if method == "md5":
        return hashlib.md5(item).hexdigest()
    elif method == "sha512":
        return hashlib.sha512(item).hexdigest()
    else:
        raise TypeError(f"method '{method}' is not a valid hash method")


def get_sp_output(cmd: list[str], default: T = None) -> Union[str, T]:
    try:
        lookup = sp.run(cmd, capture_output=True)
        lookup.check_returncode()
        return lookup.stdout.decode().strip()
    except (RuntimeError, sp.CalledProcessError):
        return default
