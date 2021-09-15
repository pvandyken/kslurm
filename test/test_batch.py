from unittest import mock
from pytest import CaptureFixture
from pathlib import Path
from kslurm.submission import kbatch

def test_batch_submits_testmode(capsys: CaptureFixture[str]):
    with mock.patch('subprocess.run') as subprocess:
        with mock.patch('sys.argv', ['kbatch', '-t', 'command']):
            kbatch()
        
        out = capsys.readouterr()
        assert "--account=ctb-akhanf --time=03:00:00 --cpus-per-task=1 --mem=4000" in str(out)
        subprocess.assert_called_once_with("echo '#!/bin/bash\ncommand' | cat", shell=True, capture_output=True)

def test_params_can_be_altered(capsys: CaptureFixture[str]):
    with mock.patch('subprocess.run') as subprocess:
        starting_cwd = Path.cwd()
        with mock.patch('sys.argv', [
            'kbatch',
            '1-33:11', 
            '5G', 
            'gpu', 
            '--account',
            'some-account',
            '-j',
            'Regular',
            './test', 
            'command'
        ]):
            kbatch()
        
        out = capsys.readouterr()
        print(str(out))
        assert "--account=some-account --time=2-09:11:00 --cpus-per-task=8 --mem=5000 --gres=gpu:1" in str(out)
        subprocess.assert_called_once_with(
            "echo '#!/bin/bash\ncommand' | sbatch --account=some-account "
            "--time=2-09:11:00 --cpus-per-task=8 --mem=5000 --gres=gpu:1 "
            "--job-name=command --parsable ", shell=True, capture_output=True)
        assert Path.cwd() == starting_cwd / 'test'