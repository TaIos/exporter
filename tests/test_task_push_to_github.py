import pytest
import flexmock

from exporter.logic import ProgressBarWrapper, TaskPushToGitHub


def blank_fn(*args, **kwargs):
    pass


@pytest.fixture()
def github():
    return flexmock(
        token='XXX',
        login='YYY',
        create_repo=blank_fn
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
        git_cmd=flexmock(create_remote=lambda: None, rev_list=lambda: None,
                         git=flexmock(rev_list=lambda: None)),
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


def test_push_happens_when_fetched_repo_has_commits(instance, monkeypatch):
    """Test if push is called when repository is correctly fetched and contains at least one commit"""

    fake_remote = flexmock(push=lambda: None)
    monkeypatch.setattr(instance.git_cmd, 'create_remote', fake_remote)
    monkeypatch.setattr(instance.git_cmd.git, 'rev_list', lambda x, y: 1)
    flexmock(fake_remote).should_receive("push").once()
    instance.run()
    assert not instance.running


def test_push_doesnt_happen_when_fetched_repo_has_zero_commits(instance, monkeypatch):
    """Test if push is not called when repository is correctly fetched and contains zero commits"""

    def raise_(*args, **kwargs):
        raise Exception()

    fake_remote = flexmock(push=raise_)
    monkeypatch.setattr(instance.git_cmd, 'create_remote', fake_remote)
    monkeypatch.setattr(instance.git_cmd.git, 'rev_list', lambda x, y: 0)
    instance.run()
    assert not instance.running
