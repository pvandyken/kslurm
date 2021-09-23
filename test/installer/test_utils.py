from __future__ import absolute_import

import os
import shutil
import site
import tempfile
from pathlib import Path
from unittest.mock import call, mock_open

from pytest import fixture
from pytest_mock import MockerFixture

import kslurm.installer.utils as utils


@fixture
def venv(mocker: MockerFixture):
    dir = Path(tempfile.gettempdir()) / "temp-library"

    bin_dir = dir / "venv" / "bin"
    bin_dir.mkdir(parents=True)
    (dir / "VERSION").touch()
    p_exec = bin_dir / "python"
    p_exec.touch()
    mocker.patch("sys.executable", p_exec)

    yield dir

    shutil.rmtree(dir)


@fixture
def envvar_dir(mocker: MockerFixture):
    dir = tempfile.gettempdir() + "/venv"
    mocker.patch("os.getenv", return_value=dir)
    return Path(dir)


class TestDataDir:
    HOME_DIR = "TESTING_DATA_DIRECTORY"

    def test_returns_current_venv_if_python_executable_is_in_project_venv(
        self, venv: Path, envvar_dir: Path
    ):
        assert utils.data_dir(self.HOME_DIR) == venv

    def test_returns_home_dir_if_set(self, mocker: MockerFixture, envvar_dir: Path):
        getenv_spy = mocker.spy(os, "getenv")
        assert utils.data_dir(self.HOME_DIR) == envvar_dir
        getenv_spy.assert_called_with(self.HOME_DIR)

    def test_checks_xdg_data_if_nothing_else_set(self, mocker: MockerFixture):
        getenv_spy = mocker.spy(os, "getenv")
        assert utils.data_dir(self.HOME_DIR) == Path.home() / ".local/share/kutils"
        getenv_spy.assert_called_with("XDG_DATA_HOME", Path.home() / ".local/share")


class TestBinDir:
    HOME_DIR = "TESTING_DATA_DIRECTORY"

    def test_returns_home_dir_if_set(self, mocker: MockerFixture, envvar_dir: Path):
        getenv_spy = mocker.spy(os, "getenv")
        assert utils.bin_dir(self.HOME_DIR) == envvar_dir / "bin"
        getenv_spy.assert_called_with(self.HOME_DIR)

    def test_returns_default_otherwise(self):
        assert utils.bin_dir(self.HOME_DIR) == Path(site.getuserbase()) / "bin"


def test_get(mocker: MockerFixture):
    mockopen = mock_open(read_data="Hello World")
    urlopen = mocker.patch("kslurm.installer.utils.closing", mockopen)
    text = utils.get("http://google.com")

    assert call().read() in urlopen.mock_calls
    assert text == "Hello World"
