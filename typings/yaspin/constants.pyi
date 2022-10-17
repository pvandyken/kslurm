from __future__ import absolute_import

from typing import Literal

Attr = (
    Literal["blink"]
    | Literal["bold"]
    | Literal["concealed"]
    | Literal["dark"]
    | Literal["reverse"]
    | Literal["underline"]
)
Color = (
    Literal["blue"]
    | Literal["cyan"]
    | Literal["green"]
    | Literal["magenta"]
    | Literal["red"]
    | Literal["white"]
    | Literal["yellow"]
)
OnColor = (
    Literal["on_blue"]
    | Literal["on_cyan"]
    | Literal["on_green"]
    | Literal["on_grey"]
    | Literal["on_magenta"]
    | Literal["on_red"]
    | Literal["on_white"]
    | Literal["on_yellow"]
)
Side = Literal["left"] | Literal["right"]

ENCODING: str
COLOR_MAP: dict[Attr | Color | OnColor, str]
COLOR_ATTRS: list[Attr | Color | OnColor]
SPINNER_ATTRS: list[str]
