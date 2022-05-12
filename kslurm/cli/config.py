from __future__ import absolute_import

import re
import subprocess as sp
from typing import Any, DefaultDict

from InquirerPy import inquirer as inq  # type: ignore
from InquirerPy.base import Choice  # type: ignore

import kslurm.appconfig as appconfig
from kslurm.args import flag, positional
from kslurm.args.command import CommandError, command


class InteractiveConfigError(CommandError):
    pass


def _get_account_type(
    accounts: dict[str, set[str]], levelfs: dict[str, str], label: str
) -> str:
    choices: list[Any] = [
        Choice(account, f"{account} (LevelFS: {levelfs[account + '_' + label]})")
        for account, types in accounts.items()
        if label in types
    ]
    if not choices:
        print(f"No {label}-enabled accounts available. Skipping.")
        return ""
    elif len(choices) == 1:
        print(f"One {label}-enabled account available: {choices[0]}")
        return choices[0].value
    else:
        return inq.fuzzy(
            f"Select an account for {label} jobs. Higher LevelFS is better.",
            choices=choices,
        ).execute()


def _account():
    whoami = sp.run(["whoami"], capture_output=True).stdout.decode().strip()
    proc = sp.run(
        [
            "sacctmgr",
            "list",
            "user",
            "WithAssoc",
            f"Names={whoami}",
            "Format=Account",
            "-Pn",
        ],
        capture_output=True,
    )
    if proc.returncode != 0:
        raise InteractiveConfigError(
            "sacctmgr command not available. Cannot interactively set account."
        )
    accounts = set(proc.stdout.decode().strip().splitlines())
    account_types: dict[str, set[str]] = DefaultDict(set)
    account_fs: dict[str, str] = {}
    for account in accounts:
        if not (match := re.match(r"^([\w\-]+)_(cpu|gpu)$", account)):
            continue
        account_fs[account] = (
            sp.run(
                ["sshare", "-A", account, "-o", "LevelFS", "-hP"], capture_output=True
            )
            .stdout.decode()
            .strip()
            .splitlines()[0]
        )
        account_types[match[1]].add(match[2])
    if not account_types:
        raise InteractiveConfigError(
            "No accounts found using sacctmgr. Cannot interactively set account."
        )
    cpu_choice = _get_account_type(account_types, account_fs, "cpu")
    gpu_choice = _get_account_type(account_types, account_fs, "gpu")
    return {"account.gpu": gpu_choice, "account.cpu": cpu_choice, "account": None}


INTERACTIVE_SETTINGS = {"account": _account}


@command(inline=True)
def config(
    entry: str = positional(help="Configuration value to update"),
    value: str = positional(
        default="",
        help="Updated value for config entry. If not provided, the current config "
        "value is printed",
    ),
    interactive: bool = flag(["--interactive", "-i"]),
):
    """Read and write from the kslurm config"""
    config = appconfig.Config()
    if interactive:
        if entry not in INTERACTIVE_SETTINGS:
            raise InteractiveConfigError(f"{entry} can not be updated interactively")
        for key, new_value in INTERACTIVE_SETTINGS[entry]().items():
            if new_value is not None:
                config[key] = new_value
                continue
            if key in config:
                del config[key]
        config.write()
        return
    if not value:
        curr_value = config.get(entry)
        if curr_value is not None:
            print(curr_value)
        for key, value in config.get_children(entry):
            print(f"{key}: {value}")

    else:
        config[entry] = value
        config.write()
