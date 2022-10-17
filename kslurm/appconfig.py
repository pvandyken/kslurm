from __future__ import absolute_import, annotations

import json
from collections import UserDict
from pathlib import Path

import appdirs

from kslurm.args.command import CommandError

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


class InvalidPipdirError(CommandError):
    pass


class PipDir(type(Path())):
    def __new__(cls):
        pipdir = Config().get("pipdir")
        if pipdir is None:
            raise InvalidPipdirError(
                "pipdir not set. Please set pipdir using `kslurm config pipdir "
                "<directory>`, typically to a project-space or permanent storage "
                "directory"
            )
        pipdir = Path(pipdir)
        try:
            pipdir.mkdir(exist_ok=True)
        except FileNotFoundError:
            raise InvalidPipdirError(
                f"Unable to create pipdir in non-existant directory '{pipdir.parent}'. "
                "Please manually create this directory."
            )
        return super().__new__(cls, pipdir)
