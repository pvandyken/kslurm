from __future__ import annotations
from typing import Optional

class CommandLineError(Exception):
    def __init__(self, msg: str, src_err: Optional[ValidationError] = None):
        super().__init__(msg)
        self.msg = msg
        self.src_err = src_err

class ValidationError(Exception):
    def __init__(self, msg: str):
        super().__init__(msg)
        self.msg = msg

class TemplateError(Exception):
    def __init__(self, msg: str):
        super().__init__(msg)
        self.msg = msg