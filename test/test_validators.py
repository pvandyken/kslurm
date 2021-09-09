import cluster_utils.slurm.slurm_args.validators as validators
import pytest

def test_job_template_validator():
    should_work = [
        "16core64gb24h",
        "Fat",
        "Regular"
    ]
    shouldnt_work = [
        "random",
        "nonsense",
        "notfound"
    ]

    for x in should_work:
        assert validators.job_template(x)
    for x in shouldnt_work:
        with pytest.raises(Exception):
            validators.job_template(x)