from __future__ import absolute_import

import json
import re
from collections import UserDict
from pathlib import Path

from kslurm.appconfig import Config
from kslurm.args.command import CommandError


class MissingPipdirError(CommandError):
    pass


class KpyIndex(UserDict[str, str]):
    def __init__(self, slurm_tmpdir: Path):
        self._path = slurm_tmpdir / "tmp" / "kpy-index.json"
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

    def __str__(self):
        return "• " + "\n• ".join(self.data.keys()) if self.data else ""


class VenvCache(UserDict[str, Path]):
    def __init__(self):
        pipdir = Config().get("pipdir")
        if pipdir is None:
            raise MissingPipdirError(
                "pipdir not set. Please set pipdir using `kslurm config pipdir "
                "<directory>`, typically to a project-space or permanent storage "
                "directory"
            )
        self.venv_cache = Path(pipdir, "venv_archives")
        self.venv_cache.mkdir(exist_ok=True)
        venvs_re = [
            re.search(r"(.+)\.tar\.gz$", str(f.name)) for f in self.venv_cache.iterdir()
        ]
        venvs = [r.group(1) for r in venvs_re if r]
        self.data = {v: self._construct_path(v) for v in venvs}

    def get_path(self, name: str):
        try:
            return self.data[name]
        except KeyError:
            return self._construct_path(name)

    def _construct_path(self, name: str):
        return (self.venv_cache / name).with_suffix(".tar.gz")

    def __str__(self):
        return "• " + "\n• ".join(self.data.keys()) if self.data else ""
