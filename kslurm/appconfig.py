from __future__ import absolute_import

import json
from pathlib import Path
from typing import Dict, Optional

import appdirs

_STATE: Dict[str, Dict[str, str]] = {"config": {}}

CONFIG_PATH = Path(appdirs.user_config_dir("kslurm"), "config.json")


def _load_config():
    if not _STATE["config"]:
        if not CONFIG_PATH.exists():
            CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
            with CONFIG_PATH.open('w') as f:
                json.dump({}, f)
        try:
            with CONFIG_PATH.open("r") as f:
                _STATE["config"] = json.load(f)
        except json.JSONDecodeError:
            print(f"Error decoding config file '{CONFIG_PATH}'")
            exit()


def get_config(entity: str) -> Optional[str]:
    _load_config()
    return _STATE["config"].get(entity, None)


def set_config(entity: str, value: str):
    _load_config()
    _STATE["config"][entity] = value
    with CONFIG_PATH.open("w") as f:
        json.dump(_STATE["config"], f)
