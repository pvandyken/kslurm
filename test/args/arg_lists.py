from __future__ import absolute_import

from typing import Any, List

from kslurm.args.arg_types import Arg, PositionalArg

from .arg_templates import Templates


class DummyArgs:
    positionals: List[PositionalArg[Any]] = [
        Templates.positional.set_value("Hello"),
        Templates.positional2.set_value("beautiful"),
        Templates.positional3.set_value("world"),
    ]

    extra_positionals: List[PositionalArg[Any]] = [
        Templates.positional.set_value("Hello"),
        Templates.positional2.set_value("beautiful"),
        Templates.positional3.set_value("world"),
        Templates.positional4.set_value("Here"),
        Templates.positional5.set_value("Be"),
        Templates.positional3.set_value("Extra!"),
    ]

    ###
    # Args used to test keyword groupping
    two_keyword: List[Arg[Any]] = [
        Templates.time,
        Templates.gpu,
        Templates.job_template,
        Templates.positional,
        Templates.time,
        Templates.length_5_keyword,
        Templates.positional,
        Templates.time,
        Templates.gpu,
        Templates.positional,
        Templates.positional,
        Templates.gpu,
        Templates.number,
        Templates.time,
    ]

    positional_patchwork: List[Arg[Any]] = [
        Templates.time,
        Templates.positional,
        Templates.number,
        Templates.positional2,
        Templates.number,
        Templates.positional3,
        Templates.gpu,
    ]

    positional_wrapped_keyword: List[Arg[Any]] = [
        Templates.time,
        Templates.positional,
        Templates.job_template,
        Templates.positional,
        Templates.positional,
    ]

    lazy_keywords: List[Arg[Any]] = [
        Templates.time,
        Templates.positional,
        Templates.lazy_inf_keyword,
        Templates.positional,
        Templates.positional,
        Templates.lazy_inf_keyword,
        Templates.positional,
        Templates.positional,
        Templates.positional,
        Templates.positional,
        Templates.time,
    ]

    greedy_keywords: List[Arg[Any]] = [
        Templates.time,
        Templates.gpu,
        Templates.greedy_inf_keyword,
        Templates.positional,
        Templates.time,
        Templates.lazy_inf_keyword,
        Templates.time,
        Templates.positional,
        Templates.time,
    ]


class ArgStr:
    positionals: List[str] = ["Hello", "beautiful", "world"]

    extra_positionals: List[str] = [
        "Hello",
        "beautiful",
        "world",
        "Here",
        "be",
        "extra",
    ]

    two_keyword: List[str] = [
        "07:23",
        "gpu",
        "--job-template",
        "parcour",
        "3",
        "--length_5_keyword",
        "one",
        "of",
        "the",
        "five",
        "values",
        "command",
    ]

    shapes_and_positionals: List[str] = [
        "07:23",
        "gpu",
        "--job-template",
        "parcour",
        "one",
        "of" "3",
        "the",
        "five",
        "values",
        "command",
    ]
