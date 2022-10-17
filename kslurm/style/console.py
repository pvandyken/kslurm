from __future__ import absolute_import, annotations

from rich.console import Console

from kslurm.style.themes import default

console = Console(theme=default)
stderr = Console(theme=default, stderr=True)
