from pytest import fixture
from typing import List, cast
import functools as ft
import cluster_utils.utils.slurm_command as sc
from cluster_utils.args import Arg, ShapeArg, KeywordArg
import cluster_utils.args as arglib


@fixture
def slurm_args():
    return [
        ShapeArg("time", "2-00:00"),
        ShapeArg("cpu", "22"),
        KeywordArg("job template", "--job-template", 1),
        ShapeArg(arglib.COMMAND, "template"),
        ShapeArg(arglib.MEM,"5G"),
        KeywordArg("Size5Keyword", "--different-template", 5),
        ShapeArg(arglib.COMMAND, "arg1"),
        ShapeArg(arglib.TIME, "arg2"),
        ShapeArg(arglib.GPU, "arg3"),
        ShapeArg(arglib.JUPYTER, "arg4"),
        ShapeArg(arglib.TEST, "-t"),
        ShapeArg(arglib.COMMAND, "command")
    ]

def test_get_keywork_group_size(slurm_args: List[Arg]):
    group_sizes = [sc.get_keyword_group_size(arg) for arg in slurm_args]
    assert group_sizes == [0, 0, 1, 0, 0, 5, 0, 0, 0, 0, 0, 0]

class TestGetNonKeywords:
    def _reduce_arg_list(self, args: List[Arg]):
        return  ft.reduce(
                    sc.get_non_keywords, args, (0, cast(List[Arg], []))
                )
    
    def test_collects_nonkeyword_into_empty_running_list(self, slurm_args: List[Arg]):
        group_size, arg_list = sc.get_non_keywords((0, []), slurm_args[0]) 
        assert group_size == 0
        assert list(arg_list) == [slurm_args[0]]
    
    def test_skips_keyword_and_updates_group_number(self, slurm_args: List[Arg]):
        group_size, arg_list = sc.get_non_keywords((0, []), slurm_args[2])
        assert group_size == 1
        assert list(arg_list) == []

    def test_skips_args_beyond_keyword_according_to_group_size(self, slurm_args: List[Arg]):
        first = sc.get_non_keywords((0, []), slurm_args[2])
        group_size, arg_list = sc.get_non_keywords(first, slurm_args[3])
        assert group_size == 0
        assert list(arg_list) == []

        first = sc.get_non_keywords((0, []), slurm_args[5])
        second = sc.get_non_keywords(first, slurm_args[6])
        third = sc.get_non_keywords(second, slurm_args[7])
        fourth = sc.get_non_keywords(third, slurm_args[8])
        fifth = sc.get_non_keywords(fourth, slurm_args[9])
        group_size, arg_list = sc.get_non_keywords(fifth, slurm_args[10])
        assert group_size == 0
        assert list(arg_list) == []

    def test_can_use_reduce_to_traverse_long_arg_lists(self, slurm_args: List[Arg]):
        group_size, arg_list = \
            self._reduce_arg_list(slurm_args[5:6])
        assert group_size == 5
        assert list(arg_list) == []

        group_size, arg_list = \
            self._reduce_arg_list(slurm_args[5:11])
        assert group_size == 0
        assert list(arg_list) == []

    def test_continues_collecting_when_past_keyword_group(self, slurm_args: List[Arg]):
        group_size, arg_list = \
            self._reduce_arg_list(slurm_args)
        assert group_size == 0
        assert list(arg_list) == [
            ShapeArg("time", "2-00:00"),
            ShapeArg("cpu", "22"),
            ShapeArg(arglib.MEM,"5G"),
            ShapeArg(arglib.COMMAND, "command")
        ]


def test_that_keywords_are_extracted(slurm_args: List[Arg]):

    positional, keywords = sc.extract_keywords(slurm_args)

    assert list(positional) == [
        ShapeArg("time", "2-00:00"),
        ShapeArg("cpu", "22"),
        ShapeArg(arglib.MEM,"5G"),
        ShapeArg(arglib.COMMAND, "command")
    ]

    assert list(keywords) == [
        [
            KeywordArg("job template", "--job-template", 1),
            ShapeArg(arglib.COMMAND, "template")
        ],
        [
            KeywordArg("Size5Keyword", "--different-template", 5),
            ShapeArg(arglib.COMMAND, "arg1"),
            ShapeArg(arglib.TIME, "arg2"),
            ShapeArg(arglib.GPU, "arg3"),
            ShapeArg(arglib.JUPYTER, "arg4"),
            ShapeArg(arglib.TEST, "-t"),
        ]
    ]

class TestDelineateCommand:
    def test_splits_list_at_first_command(self, slurm_args: List[Arg]):
        args, command = sc.delineate_command(slurm_args)

        assert list(args) == [
            ShapeArg("time", "2-00:00"),
            ShapeArg("cpu", "22"),
            KeywordArg("job template", "--job-template", 1),
        ]

        assert list(command) == [
            ShapeArg(arglib.COMMAND, "template"),
            ShapeArg(arglib.MEM,"5G"),
            KeywordArg("Size5Keyword", "--different-template", 5),
            ShapeArg(arglib.COMMAND, "arg1"),
            ShapeArg(arglib.TIME, "arg2"),
            ShapeArg(arglib.GPU, "arg3"),
            ShapeArg(arglib.JUPYTER, "arg4"),
            ShapeArg(arglib.TEST, "-t"),
            ShapeArg(arglib.COMMAND, "command")
        ]
    def test_splits_after_keyword_extraction(self, slurm_args: List[Arg]):
        
        positional, _ = sc.extract_keywords(slurm_args) # type: ignore
        
        args, command = sc.delineate_command(positional)

        
        assert list(args) == [
            ShapeArg("time", "2-00:00"),
            ShapeArg("cpu", "22"),
            ShapeArg(arglib.MEM,"5G")
        ]

        assert list(command) == [
            ShapeArg(arglib.COMMAND, "command")
        ]