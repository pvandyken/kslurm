from cluster_utils.args.arg_types import ShapeArg, KeywordArg, PositionalArg, TailArg
import re

def time(time: str):
    if '-' in time:
        days, hhmm = time.split('-')
        hours, min = hhmm.split(':')
    else:
        days = 0
        hours, min = time.split(':')
    return str(int(min) + int(hours)*60 + int(days)*60*24)

class AttrModel:
    time: ShapeArg[str] = ShapeArg(
        id = "random",
        match = lambda arg: bool(re.match(r'^([0-9]{1,2}-)?[0-9]{1,2}:[0-9]{2}$', arg)),
        format = time,
        value = "03:00")

    gpu: ShapeArg[str] = ShapeArg(
        match = lambda arg: arg == "gpu",
        value="gpu")

    cpu: ShapeArg[str] = ShapeArg(
        match = lambda arg: bool(re.match(r'^[0-9]+$', arg)),
        value = "1")

    job_template: KeywordArg[str] = KeywordArg[str](
        id="junk", 
        match=lambda arg : arg == '-j' or arg == '--job-template',
        num=1,
        value="job_template")

    length_5_keyword: KeywordArg[str] = KeywordArg[str](
        id="length_5_keyword",
        match=lambda arg: arg == "--length_5_keyword",
        num=5,
        value="length_5_keyword"
    )

    lazy_inf_keyword: KeywordArg[str] = KeywordArg[str](
        id="lazy_inf_keyword",
        match = lambda arg: arg == "lazy_inf_keyword",
        num = 0,
        value="lazy_inf_keyword"
    )

    greedy_inf_keyword: KeywordArg[str] = KeywordArg[str](
        id="greedy_inf_keyword",
        match = lambda arg: arg == "greedy_inf_keyword",
        num = -1,
        value="greedy_inf_keyword"
    )

    positional: PositionalArg = PositionalArg(
        id="positional",
        value = 'pos1'
    )

    positional2: PositionalArg = PositionalArg(
        id="positional2",
        value = 'pos2'
    )

    positional3: PositionalArg = PositionalArg(
        id="positional3",
        value = 'pos3'
    )

    positional4: PositionalArg = PositionalArg(
        id="positional4",
        value = 'pos4'
    )

    positional5: PositionalArg = PositionalArg(
        id="positional5",
        value = 'pos5'
    )
    
    tail: TailArg = TailArg()

