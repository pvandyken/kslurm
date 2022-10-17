from __future__ import absolute_import

from types import FrameType
from typing import Callable

from .base_spinner import Spinner

SignalHandler = Callable[[int, FrameType, Spinner], None]

def default_handler(signum: int, frame: FrameType, spinner: Spinner) -> None: ...
def fancy_handler(signum: int, frame: FrameType, spinner: Spinner) -> None: ...
