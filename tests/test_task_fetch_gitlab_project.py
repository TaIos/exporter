import pytest
import flexmock

from exporter.logic import TaskFetchGitlabProject, ProgressBarWrapper


@pytest.fixture()
def bar():
    fake_bar = flexmock(
        update=lambda: None,
        refresh=lambda: None,
        close=lambda: None,
        unit=None,
        count=None
    )
    return ProgressBarWrapper(bar=fake_bar, initial_message='TEST')


@pytest.fixture()
def instance(bar, tmp_path):
    return TaskFetchGitlabProject(
        gitlab=None,
        name_gitlab='TEST',
        base_dir=tmp_path,
        bar=bar,
        suppress_exceptions=False,
        debug=False
    )


def test_multiple_gitlab_projects_exist(instance):
    ...


def test_no_gitlab_project_exist():
    ...


def test_error_during_cloning_gitlab_repo():
    ...


def test_error_during_git_lfs_cloning():
    ...


def test_append_caught_exception():
    ...


def test_printing_error_in_debug_mode():
    ...


def test_rethrowing_exception():
    ...


def test_interrupt():
    ...
