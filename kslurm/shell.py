from __future__ import absolute_import, annotations

import importlib.resources as impr
import os
import subprocess as sp
import tempfile
from pathlib import Path

from shellingham import ShellDetectionFailure, detect_shell


class Shell:
    """
    Represents the current shell.
    """

    _shell = None

    def __init__(self, name: str, path: str) -> None:
        self._name = name
        self._path = path

    @property
    def name(self) -> str:
        return self._name

    @property
    def path(self) -> str:
        return self._path

    @classmethod
    def get(cls) -> Shell:
        """
        Retrieve the current shell.
        """
        if cls._shell is not None:
            return cls._shell

        try:
            name, path = detect_shell(os.getpid())
        except (RuntimeError, ShellDetectionFailure):
            shell = None

            if os.name == "posix":
                shell = os.environ.get("SHELL")
            elif os.name == "nt":
                shell = os.environ.get("COMSPEC")

            if not shell:
                raise RuntimeError("Unable to detect the current shell.")

            name, path = Path(shell).stem, shell

        if name != "bash":
            print("At this time, only bash shell is supported.")
            exe = sp.run(["command", "-v", "bash"], capture_output=True)
            try:
                exe.check_returncode()
            except sp.CalledProcessError:
                print("No bash executable found on $PATH. Aborting")
            name = "bash"
            path = exe.stdout.decode()

        cls._shell = cls(name, path)

        return cls._shell

    def activate(self, env: Path):
        activate_script = self._get_activate_script()
        activate_path = env / "bin" / activate_script

        if self._name == "bash":
            with impr.path("kslurm.bin", "kpy-init.sh") as path:
                os.environ["activate_path"] = str(activate_path)
                os.environ["kslurm_next_cmd"] = tempfile.mkstemp(prefix="kslurm")[1]
                session = sp.run([self._path, "--init-file", path.resolve()])
            cmd = None
            if session.returncode == 224:
                with open(os.environ["kslurm_next_cmd"]) as f:
                    cmd = f.read().split()
                if cmd[0] != "kpy":
                    cmd = None
            os.remove(os.environ["kslurm_next_cmd"])
            del os.environ["kslurm_next_cmd"]
            del os.environ["activate_path"]
            return cmd

    def _get_activate_script(self) -> str:
        if self._name == "fish":
            suffix = ".fish"
        elif self._name in ("csh", "tcsh"):
            suffix = ".csh"
        elif self._name in ("powershell", "pwsh"):
            suffix = ".ps1"
        elif self._name == "cmd":
            suffix = ".bat"
        else:
            suffix = ""

        return "activate" + suffix

    def _get_source_command(self) -> str:
        if self._name in ("fish", "csh", "tcsh"):
            return "source"
        return "."

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}("{self._name}", "{self._path}")'
