from __future__ import absolute_import

import json
from collections import UserDict
from pathlib import Path

import appdirs

CONFIG_PATH = Path(appdirs.user_config_dir("kslurm"), "config.json")


class Config(UserDict[str, str]):
    def __init__(self):
        self._path = CONFIG_PATH
        if not self._path.exists():
            self._path.parent.mkdir(parents=True, exist_ok=True)
            with self._path.open("w") as f:
                json.dump({}, f)
                self.data = {}
        else:
            with self._path.open("r") as f:
                self.data = json.load(f)

    def write(self):
        with self._path.open("w") as f:
            json.dump(self.data, f)

    def get_children(self, entity: str):
        for key, value in self.data.items():
            if key.startswith(entity + "."):
                yield key, value

    def __str__(self):
        return "• " + "\n• ".join(self.data.keys()) if self.data else ""
