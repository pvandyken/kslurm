from __future__ import absolute_import

import hashlib
from typing import Union


def get_hash(item: Union[str, bytes], method: str = "md5"):
    if isinstance(item, str):
        item = item.encode()
    if method == "md5":
        return hashlib.md5(item).hexdigest()
    elif method == "sha512":
        return hashlib.sha512(item).hexdigest()
    else:
        raise TypeError(f"method '{method}' is not a valid hash method")
