from __future__ import absolute_import, annotations

import json
import os
import re
import subprocess as sp
from collections import UserDict
from pathlib import Path
from typing import Any

from virtualenv.create import pyenv_cfg  # type: ignore

from kslurm.appconfig import PipDir
from kslurm.utils import get_hash


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
        pipdir = PipDir()
        self.venv_cache = pipdir / "venv_archives"
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


def _pip_freeze(venv_dir: Path):
    return sp.run(
        [venv_dir / "bin" / "python", "-m", "pip", "freeze"], capture_output=True
    ).stdout


def _file_sub(path: Path, *replacements: tuple[str, str]):
    with path.open("r") as f:
        contents = f.read()
    sub = contents
    for replace in replacements:
        sub = re.sub(*replace, sub)
    with path.open("w") as f:
        f.write(sub)


class PromptRefreshError(Exception):
    pass


class VenvPrompt:
    def __init__(self, venv_dir: Path):
        self.cfg: Any = pyenv_cfg.PyEnvCfg.from_folder(venv_dir)  # type: ignore
        self.venv_dir = venv_dir
        try:
            self.name = self.cfg["prompt"]
        except KeyError:
            self.name = "venv"

    def update_prompt(self, name: str):
        self.name = name
        self.cfg["prompt"] = name

    def update_hash(self):
        self.cfg["state_hash"] = get_hash(_pip_freeze(self.venv_dir))

    def refresh(self):
        try:
            state_hash = self.cfg["state_hash"]
        except KeyError:
            raise PromptRefreshError()

        try:
            hsh = get_hash(_pip_freeze(self.venv_dir))
            if hsh != state_hash and self.name[0] != "*":
                self.update_prompt("*" + self.name)
            elif hsh == state_hash and self.name[0] == "*":
                self.update_prompt(self.name[1:])
            self.save()
        except KeyError:
            raise PromptRefreshError()

    def save(self):
        self.cfg.write()
        bin_dir = self.venv_dir / "bin"
        _file_sub(
            bin_dir / "activate",
            (
                r'\[\s"x[^"$]*"\s!=\sx\s\]',
                f'[ "x{self.name}" != x ]',
            ),
            (r'\sPS1="[^"$]*\$\{PS1\-\}"', f' PS1="({self.name}) ${{PS1-}}"'),
        )

        # _file_sub(
        #     r"\(\x27[^\x27]*\x27\s!=\s\x22\x22\)",
        #     f"('{self.name}' != \"\")",
        #     bin_dir / "activate.csh",
        # )

        # _file_sub(
        #     r"\(\x27[^\x27]*\x27\s!=\s\x22\x22\)",
        #     f"('{self.name}' != \"\")",
        #     bin_dir / "activate.csh",
        # )


def rebase_venv(venv_dir: Path):
    with (venv_dir / "bin" / "activate").open("r") as f:
        resolved = venv_dir.resolve()
        lines = f.read().splitlines()
        # \x22 and \x27 are " and ' char
        subbed = [
            re.sub(
                r"(?<=^VIRTUAL_ENV=([\x22\x27])).*(?=\1$)",
                str(resolved),
                line,
            )
            for line in lines
        ]
    with (venv_dir / "bin" / "activate").open("w") as f:
        f.write("\n".join(subbed))

    for root, _, files in os.walk(venv_dir / "bin"):
        for file in files:
            path = Path(root, file)
            if path.is_symlink() or not os.access(path, os.X_OK):
                continue
            with path.open("r") as f:
                lines = f.read().splitlines()
                try:
                    subbed = [
                        re.sub(
                            r"(?<=^#!)\/.*python.*$",
                            str(resolved / "bin" / "python"),
                            lines[0],
                        ),
                        *lines[1:],
                    ]
                except IndexError:
                    subbed = lines
            with path.open("w") as f:
                f.write("\n".join(subbed))
