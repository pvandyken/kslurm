# from __future__ import absolute_import

# from typing import Any, List

from __future__ import absolute_import

# from kslurm.args.arg import Arg
# from .arg_templates import Templates


# class DummyArgs:

#     ###
#     # Args used to test keyword groupping
#     two_keyword: List[Arg[Any, Any]] = [
#         Templates.time,
#         Templates.gpu,
#         Templates.job_template,
#         Templates.positional1,
#         Templates.time,
#         Templates.length_5_keyword,
#         Templates.positional1,
#         Templates.time,
#         Templates.gpu,
#         Templates.positional1,
#         Templates.positional1,
#         Templates.gpu,
#         Templates.number,
#         Templates.time,
#     ]

#     positional_patchwork: List[Arg[Any, Any]] = [
#         Templates.positional1,
#         Templates.positional2,
#         Templates.positional3,
#     ]

#     positional_wrapped_keyword: List[Arg[Any, Any]] = [
#         Templates.positional1,
#         Templates.job_template,
#         Templates.positional1,
#         Templates.positional1,
#     ]

#     lazy_keywords: List[Arg[Any, Any]] = [
#         Templates.positional1,
#         Templates.lazy_inf_keyword,
#         Templates.positional1,
#         Templates.positional1,
#         Templates.lazy_inf_keyword,
#         Templates.positional1,
#         Templates.positional1,
#         Templates.positional1,
#         Templates.positional1,
#         Templates.time,
#     ]

#     greedy_keywords: List[Arg[Any, Any]] = [
#         Templates.greedy_inf_keyword,
#         Templates.lazy_inf_keyword,
#         Templates.positional1,
#         Templates.time,
#     ]


# class ArgStr:
#     positionals: List[str] = ["Hello", "beautiful", "world"]

#     extra_positionals: List[str] = [
#         "Hello",
#         "beautiful",
#         "world",
#         "Here",
#         "be",
#         "extra",
#     ]

#     two_keyword: List[str] = [
#         "07:23",
#         "gpu",
#         "--job-template",
#         "parcour",
#         "3",
#         "--length_5_keyword",
#         "one",
#         "of",
#         "the",
#         "five",
#         "values",
#         "command",
#     ]

#     shapes_and_positionals: List[str] = [
#         "07:23",
#         "gpu",
#         "--job-template",
#         "parcour",
#         "one",
#         "of" "3",
#         "the",
#         "five",
#         "values",
#         "command",
#     ]
