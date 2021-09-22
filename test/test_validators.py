from __future__ import absolute_import

import pytest

import kslurm.models.validators as validators
from kslurm.exceptions import TemplateError


class TestJobTemplateValidator:
    @pytest.mark.parametrize("arg", ["16core64gb24h", "Fat", "Regular"])
    def test_args_that_should_work(self, arg: str):
        assert validators.job_template(arg)

    @pytest.mark.parametrize("arg", ["random", "nonsense", "notfound"])
    def test_args_that_shouldnt_work(self, arg: str):
        with pytest.raises(TemplateError):
            assert not validators.job_template(arg)
