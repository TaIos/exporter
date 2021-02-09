import git
import pytest
import flexmock

from exporter.exeptions import MultipleGitLabProjectsExistException, NoGitLabProjectsExistException
from exporter.logic import TaskFetchGitlabProject, ProgressBarWrapper, TaskPushToGitHub


@pytest.fixture()
def github():
    return flexmock(
        token='XXX',
        login='YYY',
        create_repo=lambda: None
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
def instance(github, bar, tmp_path):
    return TaskPushToGitHub(
        github=github,
        git_cmd=None,
        name_github='TEST',
        is_private=False,
        bar=bar,
        suppress_exceptions=False,
        debug=False
    )


def test_error_during_creating_github_repo(instance, monkeypatch):
    """Test flags and state after errors raised by creating GitHub repository"""

    def raise_(*args, **kwargs):
        raise Exception('ABC')

    with pytest.raises(Exception, match='ABC'):
        monkeypatch.setattr(instance.github, 'create_repo', raise_)
        instance.suppress_exceptions = False
        instance.run()

    assert not instance.running
    assert len(instance.exc) == 1
    assert str(instance.exc[0]) == 'ABC'
