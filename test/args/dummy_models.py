from typing_extensions import TypedDict
from kslurm.args.arg_types import ShapeArg, KeywordArg, TailArg, PositionalArg
import re
import attr

def time(time: str):
    if ':' in time:
        if '-' in time:
            days, hhmm = time.split('-')
            hours, min = hhmm.split(':')
        else:
            days = 0
            hours, min = time.split(':')
    else:
        try:
            min = int(time)
            hours, days = 0, 0
        except:
            raise TypeError(f"Invalid format for time: \"{time}\"\n"
                            f"Must be as [xx-]xx:xx or x where x is a number")
    return str(int(min) + int(hours)*60 + int(days)*60*24)

@attr.s(auto_attribs=True)
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

    job_template: KeywordArg[str] = KeywordArg(
        id="junk", 
        match=['-j', '--job-template'],
        num=1,
        value=False)

    length_5_keyword: KeywordArg[str] = KeywordArg(
        id="length_5_keyword",
        match=['--length_5_keyword'],
        num=5,
        value=False
    )

    tail: TailArg = TailArg()

class TypedDictModel(TypedDict):
    time: ShapeArg[str]
    gpu: ShapeArg[str]
    cpu: ShapeArg[str]
    job_template: KeywordArg[str] 
    length_5_keyword: KeywordArg[str] 
    tail: TailArg

typed_dict_model = TypedDictModel(
    time= ShapeArg(
        id = "random",
        match = lambda arg: bool(re.match(r'^([0-9]{1,2}-)?[0-9]{1,2}:[0-9]{2}$', arg)),
        format = time,
        value = "03:00"),

    gpu= ShapeArg(
        match = lambda arg: arg == "gpu",
        value="gpu"),

    cpu= ShapeArg(
        match = lambda arg: bool(re.match(r'^[0-9]+$', arg)),
        value = "1"),

    job_template = KeywordArg[str](
        id="junk", 
        match=['-j', '--job-template'],
        num=1,
        value=False),

    length_5_keyword = KeywordArg[str](
        id="length_5_keyword",
        match=['--length_5_keyword'],
        num=5,
        value=False
    ),

    tail = TailArg()
)

@attr.s(auto_attribs=True)
class PositionalAndShapeModel:
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

    job_template: KeywordArg[str] = KeywordArg(
        id="junk", 
        match=['-j', '--job-template'],
        num=1,
        value=False)

    positional: PositionalArg[str] = PositionalArg(
        id="positional",
        value = 'pos1'
    )

    positional2: PositionalArg[str] = PositionalArg(
        id="positional2",
        value = 'pos2'
    )

    positional3: PositionalArg[str] = PositionalArg(
        id="positional3",
        value = 'pos3'
    )

    tail: TailArg = TailArg()