# # pyright: reportPrivateUsage=false
# from __future__ import absolute_import

from __future__ import absolute_import

# from pathlib import Path
# from pytest_mock import MockerFixture

# import kslurm.installer.installer as installer


# class TestMakeEnv:
#     def test_creates_new_venv(self, mocker: MockerFixture, tmp_path: Path):
#         envbuilder = mocker.patch.object(installer, "EnvBuilder")
#         assert installer._make_env(tmp_path) == tmp_path / "venv"
#         envbuilder.assert_called_once()

#     def test_doesnt_create_venv_if_update_and_venv_exists(
#         self, mocker: MockerFixture, tmp_path: Path
#     ):
#         envbuilder = mocker.patch.object(installer, "EnvBuilder")
#         mocker.patch.object(installer, "_is_venv", return_value=True)
#         assert installer._make_env(tmp_path, True) == tmp_path / "venv"
#         envbuilder.assert_not_called()

#     def test_creates_venv_if_venv_exists_but_update_not_true(
#         self, mocker: MockerFixture, tmp_path: Path
#     ):
#         envbuilder = mocker.patch.object(installer, "EnvBuilder")
#         mocker.patch.object(installer, "_is_venv", return_value=True)
#         assert installer._make_env(tmp_path) == tmp_path / "venv"
#         envbuilder.assert_called_once()

#     def test_creates_venv_if_update_but_no_existing_venv(
#         self, mocker: MockerFixture, tmp_path: Path
#     ):
#         envbuilder = mocker.patch.object(installer, "EnvBuilder")
#         assert installer._make_env(tmp_path, True) == tmp_path / "venv"
#         envbuilder.assert_called_once()


# def test_install_library(mocker: MockerFixture, tmp_path: Path):
#     sub = mocker.patch("subprocess.run")
#     installer._install_library("pkg==3.2", tmp_path)
#     sub.assert_called_once()
