from __future__ import absolute_import

from dataclasses import dataclass

@dataclass
class Spinner:
    frames: list[str]
    interval: int

default_spinner: Spinner
