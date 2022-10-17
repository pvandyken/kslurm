from __future__ import absolute_import, annotations

import json
import os
import site
from pathlib import Path
from unittest.mock import call, mock_open

from pyfakefs.fake_filesystem import FakeFilesystem
from pytest import fixture
from pytest_mock import MockerFixture

import kslurm.installer.utils as utils


@fixture
def venv(mocker: MockerFixture, fs: FakeFilesystem):
    dir = Path("/fake/path") / "temp-library"

    bin_dir = dir / "venv" / "bin"
    fs.create_dir(bin_dir)
    fs.create_file(dir / "VERSION")

    p_exec = bin_dir / "python"
    fs.create_file(p_exec)
    mocker.patch("sys.executable", p_exec)

    return dir


@fixture
def envvar_dir(mocker: MockerFixture, fs: FakeFilesystem):
    dir = "fake/path/venv"
    fs.create_dir(dir)
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


class TestGetCurrentVersion:
    def test_returns_version_file_contents_if_exist(self, fs: FakeFilesystem):
        datadir = Path("/fake/datadir")
        fs.create_dir(datadir)
        fs.create_file(datadir / "VERSION", contents="test string")

        assert utils.get_current_version(datadir) == "test string"

    def test_returns_none_if_no_version_file(self, fs: FakeFilesystem):
        datadir = Path("/fake/path")
        fs.create_dir(datadir)

        assert utils.get_current_version(datadir) is None


class TestGetVersion:
    def _mock_data(self, mocker: MockerFixture, add_version: bool = False):
        release_file = Path(__file__).parent / "fake_releases.json"
        with release_file.open() as file:
            data = json.load(file)
        if add_version:
            data["releases"]["1.2.0"] = ""
        mocker.patch("json.loads", return_value=data)
        mocker.patch.object(utils, "get")
        self.fake_url = "https://example.org"

    def test_returns_latest_non_prerelease_normally(self, mocker: MockerFixture):
        self._mock_data(mocker)
        assert utils.get_version(None, False, self.fake_url) == "1.1.10"

    def test_returns_latest_release_when_preview(self, mocker: MockerFixture):
        self._mock_data(mocker)
        assert utils.get_version(None, True, self.fake_url) == "1.2.0a2"

    def test_returns_specified_version_when_given(self, mocker: MockerFixture):
        self._mock_data(mocker)
        assert utils.get_version("1.1.1", False, self.fake_url) == "1.1.1"
        assert utils.get_version("1.0.0-b6", True, self.fake_url) == "1.0.0b6"
        assert utils.get_version("0.8.1.a0", False, self.fake_url) == "0.8.1a0"

    def test_returns_none_when_given_version_doesnt_exist(self, mocker: MockerFixture):
        self._mock_data(mocker)
        assert utils.get_version("1.2.0", True, self.fake_url) is None

    def test_returns_latest_non_dev_version_if_available(self, mocker: MockerFixture):
        self._mock_data(mocker, True)
        assert utils.get_version("1.2.0", True, self.fake_url) == "1.2.0"
