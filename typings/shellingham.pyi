from __future__ import absolute_import, annotations

class ShellDetectionFailure(Exception): ...


def detect_shell(pid: int) -> tuple[str, str]: ...
