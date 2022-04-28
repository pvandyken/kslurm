# from __future__ import absolute_import

# import re

from __future__ import absolute_import

# from kslurm.args.arg_types import flag, keyword, positional, shape
# from kslurm.args.arg import Arg

# def time_format(time: str):
#     if "-" in time:
#         days, hhmm = time.split("-")
#         hours, min = hhmm.split(":")
#     else:
#         days = 0
#         hours, min = time.split(":")
#     return str(int(min) + int(hours) * 60 + int(days) * 60 * 24)


# class Templates:
#     time: Arg[str, None] = shape(
#         match=lambda arg: bool(re.match(r"^([0-9]{1,2}-)?[0-9]{1,2}:[0-9]{2}$", arg)),
#         format=time_format,
#         default="03:00",
#     )

#     gpu: Arg[bool, None] = flag(match=["gpu"])

#     number: Arg[int, None] = shape(
#         match=lambda arg: bool(re.match(r"^[0-9]+$", arg)), default="1"
#     )

#     job_template: Arg[bool, str] = keyword(match=["-j", "--job-template"], num=1)

#     length_5_keyword: Arg[bool, str] = keyword(match=["--length_5_keyword"], num=5)

#     lazy_inf_keyword: Arg[bool, str] = keyword(
#         match=["lazy_inf_keyword"],
#         num=-1,
#         lazy=True,
#     )

#     greedy_inf_keyword: Arg[bool, str] = keyword(
#         match=["greedy_inf_keyword"],
#         num=-1,
#     )

#     positional1: Arg[str, None] = positional("pos1")
#     positional2: Arg[str, None] = positional("pos2")
#     positional3: Arg[str, None] = positional("pos3")
#     positional4: Arg[str, None] = positional("pos4")
#     positional5: Arg[str, None] = positional("pos5")
