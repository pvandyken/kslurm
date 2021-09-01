from unittest import mock
from pytest import CaptureFixture
from cluster_utils.bin.batch import main

def test_batch_submits_testmode(capsys: CaptureFixture):
    with mock.patch('subprocess.run') as subprocess:
        with mock.patch('sys.argv', ['kbatch', '-t', 'command']):
            main()
        
        out = capsys.readouterr()
        assert "--account=def-lpalaniy --time=180 --cpus-per-task=1 --mem=4000" in str(out)
        subprocess.assert_called_once_with("echo '#!/bin/bash\ncommand' | cat", shell=True)

def test_params_can_be_altered(capsys: CaptureFixture):
    with mock.patch('subprocess.run') as subprocess:
        with mock.patch('sys.argv', ['kbatch', '1-33:11', '5G', '22', 'gpu', './test', 'command']):
            main()
        
        out = capsys.readouterr()
        assert "--account=def-lpalaniy --time=3431 --cpus-per-task=22 --mem=5000 --gres=gpu:1" in str(out)
        subprocess.assert_called_once_with(
            "echo '#!/bin/bash\ncommand' | sbatch --account=def-lpalaniy "
            "--time=3431 --cpus-per-task=22 --mem=5000 --gres=gpu:1 --job-name=command --parsable ", shell=True)