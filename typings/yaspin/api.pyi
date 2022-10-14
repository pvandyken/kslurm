from __future__ import absolute_import

from signal import Signals

from .base_spinner import Spinner
from .constants import Attr, Color, OnColor
from .core import Yaspin as Yaspin
from .signal_handlers import SignalHandler

def yaspin(
    spinner: Spinner | None = ...,
    text: str | None = ...,
    color: Color | None = ...,
    on_color: OnColor | None = ...,
    attrs: list[Attr] | None = ...,
    reverseal: bool | None = ...,
    side: str | None = ...,
    sigmap: dict[Signals, SignalHandler] = ...,
    timer: bool = ...,
) -> Yaspin: ...
def kbi_safe_yaspin(
    spinner: Spinner | None = ...,
    text: str | None = ...,
    color: Color | None = ...,
    on_color: OnColor | None = ...,
    attrs: list[Attr] | None = ...,
    reverseal: bool | None = ...,
    side: str | None = ...,
    timer: bool = ...,
) -> Yaspin: ...
