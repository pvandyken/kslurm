from __future__ import absolute_import

import json
from collections import UserDict
from pathlib import Path


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
