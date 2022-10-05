from __future__ import absolute_import, annotations

import os
from pathlib import Path
from typing import NoReturn

import appdirs

from kslurm.utils import get_hash

CACHE_PATH = Path(appdirs.user_cache_dir("kslurm"))


class Cache:
    def __init__(self):
        self._path = CACHE_PATH
        self._path.mkdir(exist_ok=True)

    def get_path(self, key: str):
        return self._path / get_hash(key)

    def __getitem__(self, key: str):
        path = self.get_path(key)
        if not path.exists():
            raise KeyError(f"{key} not found")
        with path.open("r") as f:
            return f.read()

    def __setitem__(self, key: str, data: str):
        path = self.get_path(key)
        with path.open("w") as f:
            f.write(data)

    def __delitem__(self, key: str):
        path = self.get_path(key)
        if not path.exists():
            raise KeyError(f"{key} not found")
        os.remove(path)

    def __len__(self):
        return len(list(self._path.iterdir()))

    def __iter__(self) -> NoReturn:
        raise NotImplementedError()
