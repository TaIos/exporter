import git
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


def test_error_during_cloning_gitlab_repo_raises_exception_and_sets_flags(instance, monkeypatch):
    """Test flags and state after errors raised by cloning GitLab project"""

    def raise_(*args):
        raise Exception('ABC')

    with pytest.raises(Exception, match='ABC'):
        monkeypatch.setattr(instance.gitlab, 'search_owned_projects', lambda x: SEARCH_OWNED_PROJECTS_RESPONSE)
        monkeypatch.setattr(git.Repo, 'clone_from', raise_)
        instance.suppress_exceptions = False
        instance.run()

    assert not instance.running
    assert len(instance.exc) == 1
    assert str(instance.exc[0]) == 'ABC'


def test_error_during_git_lfs_cloning(instance, monkeypatch):
    """Test flags and state after errors raised by fetching additional files using git LFS"""

    def raise_(*args):
        raise Exception('ABC')

    def fake_repo(*args):
        return flexmock(
            working_dir='directory'
        )

    with pytest.raises(Exception, match='ABC'):
        monkeypatch.setattr(instance.gitlab, 'search_owned_projects', lambda x: SEARCH_OWNED_PROJECTS_RESPONSE)
        monkeypatch.setattr(git.Repo, 'clone_from', fake_repo)
        monkeypatch.setattr(git.cmd.Git, 'execute', raise_)
        instance.suppress_exceptions = False
        instance.run()

    assert not instance.running
    assert len(instance.exc) == 1
    assert str(instance.exc[0]) == 'ABC'
