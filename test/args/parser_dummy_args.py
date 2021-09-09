from cluster_utils.args.arg_types import Arg, PositionalArg
from .arg_templates import AttrModel as ArgList
from typing import List, Any

def time(time: str):
    if '-' in time:
        days, hhmm = time.split('-')
        hours, min = hhmm.split(':')
    else:
        days = 0
        hours, min = time.split(':')
    return str(int(min) + int(hours)*60 + int(days)*60*24)


class Models:
    three_positionals: List[PositionalArg[Any]] = [
        ArgList.positional,
        ArgList.positional2,
        ArgList.positional3
    ]

class DummyArgs:
    positionals: List[PositionalArg[Any]] = [
        ArgList.positional.set_value("Hello"),
        ArgList.positional2.set_value("beautiful"),
        ArgList.positional3.set_value("world"),
    ]

    extra_positionals: List[PositionalArg[Any]] = [
        ArgList.positional.set_value("Hello"),
        ArgList.positional2.set_value("beautiful"),
        ArgList.positional3.set_value("world"),
        ArgList.positional4.set_value("Here"),
        ArgList.positional5.set_value("Be"),
        ArgList.positional3.set_value("Extra!"),
    ]

    two_keyword: List[Arg[Any]] = [
        ArgList.time,
        ArgList.gpu,
        ArgList.job_template,
        ArgList.positional,
        ArgList.time,
        ArgList.length_5_keyword,
        ArgList.positional,
        ArgList.time,
        ArgList.gpu,
        ArgList.positional,
        ArgList.positional,
        ArgList.gpu,
        ArgList.positional,
        ArgList.positional
    ]

    positional_wrapped_keyword: List[Arg[Any]] = [
        ArgList.time,
        ArgList.positional,
        ArgList.job_template,
        ArgList.positional,
        ArgList.positional
    ]

    lazy_keywords: List[Arg[Any]] = [
        ArgList.time,
        ArgList.positional,
        ArgList.lazy_inf_keyword,
        ArgList.positional,
        ArgList.positional,
        ArgList.lazy_inf_keyword,
        ArgList.positional,
        ArgList.positional,
        ArgList.positional,
        ArgList.positional,
        ArgList.time
    ]

    greedy_keywords: List[Arg[Any]] = [
        ArgList.time,
        ArgList.positional,
        ArgList.greedy_inf_keyword,
        ArgList.positional,
        ArgList.time,
        ArgList.lazy_inf_keyword,
        ArgList.time,
        ArgList.positional,
        ArgList.time
    ]

class ArgStr:
    positionals: List[str] = [
        "Hello",
        "beautiful",
        "world"
    ]

    extra_positionals: List[str] = [
        "Hello",
        "beautiful",
        "world",
        "Here",
        "be",
        "extra"
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
        "command"
    ]

    shapes_and_positionals: List[str] = [
        "07:23",
        "gpu",
        "--job-template",
        "parcour",
        "one",
        "of"
        "3",
        "the",
        "five",
        "values",
        "command"
    ]
