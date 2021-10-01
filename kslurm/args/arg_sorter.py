from __future__ import absolute_import

import itertools as it
from collections import defaultdict
from typing import Any, DefaultDict, Dict, Iterable, List, TypeVar, cast

from kslurm.args.arg_types import (
    Arg,
    FlagArg,
    KeywordArg,
    PositionalArg,
    ShapeArg,
    TailArg,
)
from kslurm.exceptions import CommandLineError

T = TypeVar("T")
S = TypeVar("S", bound=Arg[Any])


def group_by_type(items: Iterable[T]) -> Dict[type, List[T]]:
    groupedDict = cast(DefaultDict[type, List[T]], defaultdict(list))
    for key, value in it.groupby(items, type):
        groupedDict[key] += list(value)
    return groupedDict


class ArgSorter:
    def __init__(self, args: Iterable[Arg[Any]]):
        self.args = list(args)
        self.grouped = group_by_type(self.args)

    @property
    def shapes(self):
        return cast(List[ShapeArg[Any]], self.grouped.get(ShapeArg, []))

    @property
    def keywords(self):
        return cast(List[KeywordArg[Any]], self.grouped.get(KeywordArg, []))

    @property
    def flags(self):
        return cast(List[FlagArg], self.grouped.get(FlagArg, []))

    @property
    def tail(self):
        tail = cast(List[TailArg], self.grouped.get(TailArg, []))
        if len(tail) > 1:
            raise CommandLineError("More than 1 TailArgs provided:" f"{tail}")
        if not tail:
            return None
        return tail[0]

    @property
    def dynamic_args(self):
        return list(it.chain(self.shapes, self.keywords, self.flags))

    @property
    def static_args(self):
        return cast(
            Iterable[PositionalArg[Any]],
            filter(lambda x: isinstance(x, PositionalArg), self.args),
        )

    @property
    def validated_args(self):
        return list(it.chain(self.static_args, self.keywords))
