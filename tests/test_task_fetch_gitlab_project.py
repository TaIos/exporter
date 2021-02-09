import pytest
import flexmock

from exporter.exeptions import MultipleGitLabProjectsExistException, NoGitLabProjectsExistException
from exporter.logic import TaskFetchGitlabProject, ProgressBarWrapper

SEARCH_OWNED_PROJECTS_RESPONSE = [
    {
        'owner': {'username': 'name'},
        'http_url_to_repo': 'http://example.com/diaspora/diaspora-client.git'
    }
]


@pytest.fixture()
def gitlab():
    return flexmock(
        search_owned_projects=lambda: SEARCH_OWNED_PROJECTS,
        token='XXX'
    )


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
def instance(gitlab, bar, tmp_path):
    return TaskFetchGitlabProject(
        gitlab=gitlab,
        name_gitlab='TEST',
        base_dir=tmp_path,
        bar=bar,
        suppress_exceptions=False,
        debug=False
    )


def test_multiple_gitlab_projects_exist_raises_exception(instance, monkeypatch):
    """Can't choose between multiple GitLab projects matching given name"""
    with pytest.raises(MultipleGitLabProjectsExistException, match=r'Multiple projects found for *'):
        monkeypatch.setattr(instance.gitlab, 'search_owned_projects', lambda x: [1, 2])
        instance.run()


def test_no_gitlab_project_exist_raises_exception(instance, monkeypatch):
    """Can't export non-existing GitLab project"""
    with pytest.raises(NoGitLabProjectsExistException, match=r'No project found for *'):
        monkeypatch.setattr(instance.gitlab, 'search_owned_projects', lambda x: [])
        instance.run()


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
