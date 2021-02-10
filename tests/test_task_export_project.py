import pytest
from flexmock import flexmock

from exporter.logic import ProgressBarWrapper, TaskExportProject, TaskFetchGitlabProject, TaskPushToGitHub


def blank_fn(*args, **kwargs):
    pass


@pytest.fixture()
def github():
    return flexmock(
        token='XXX',
        login='YYY',
        repo_exists=blank_fn,
        delete_repo=blank_fn,
    )


@pytest.fixture()
def gitlab():
    return None


@pytest.fixture()
def bar():
    fake_bar = flexmock(
        update=lambda: None,
        refresh=lambda: None,
        close=lambda: None,
        unit=None,
        count=None,
        total=None
    )
    return ProgressBarWrapper(bar=fake_bar, initial_message='TEST')


@pytest.fixture()
def instance(github, gitlab, bar, tmp_path):
    return TaskExportProject(
        gitlab=gitlab,
        github=github,
        name_gitlab='TEST_GITLAB',
        name_github='TEST_GITHUB',
        is_github_private=False,
        base_dir=tmp_path,
        bar=bar,
        conflict_policy='skip',
        suppress_exceptions=False,
        debug=False
    )


def test_if_run_is_skipped_when_repo_exists_and_policy_is_skip(instance, monkeypatch):
    """When conflict policy is set to 'skip' and GitHub project already exists, run should skipped"""

    instance.conflict_policy = 'skip'
    monkeypatch.setattr(instance.github, 'repo_exists', lambda x, y: True)
    instance.run()
    assert not instance.running
    assert len(instance.subtasks) == 0
    assert TaskExportProject.SKIPPED in instance.status
    assert TaskExportProject.SUCCESS not in instance.status
    assert len(instance.exc) == 0


def test_if_overwrite_happens_when_repo_exists_and_policy_is_overwrite(instance, monkeypatch):
    """When conflict policy is set to 'overwrite' and GitHub project already exists, it should be overwritten"""

    instance.conflict_policy = 'overwrite'
    monkeypatch.setattr(instance.github, 'repo_exists', lambda x, y: True)
    monkeypatch.setattr(instance.github, 'delete_repo', lambda x, y: None)
    flexmock(instance.github).should_receive("delete_repo").once()
    flexmock(TaskFetchGitlabProject, run=lambda: None)
    flexmock(TaskPushToGitHub, run=lambda: None)
    instance.run()
    assert not instance.running
    assert len(instance.subtasks) == 2
    assert TaskExportProject.OVERWRITTEN in instance.status
    assert TaskExportProject.SUCCESS in instance.status
    assert len(instance.exc) == 0


def test_if_rollback_deletes_repo_if_it_did_not_existed_before(instance, monkeypatch):
    """Rollback should undone everything, including deleting created GitHub repository if it did not existed before"""

    instance.github_repo_existed = False
    monkeypatch.setattr(instance.github, 'repo_exists', lambda x, y: True)
    monkeypatch.setattr(instance.github, 'delete_repo', lambda x, y: None)
    flexmock(instance.github).should_receive('delete_repo').once()
    instance.rollback()
    assert TaskExportProject.ROLLBACKED in instance.status


def test_if_rollback_doesnt_delete_repo_if_it_existed_before(instance, monkeypatch):
    """Rollback should undone everything, but not delete created GitHub repository if it did existed before"""

    def raise_(*args, **kwargs):
        raise Exception('ABC')

    instance.github_repo_existed = True
    monkeypatch.setattr(instance.github, 'repo_exists', lambda x, y: False)
    monkeypatch.setattr(instance.github, 'delete_repo', lambda x, y: raise_)
    instance.rollback()
    assert TaskExportProject.ROLLBACKED in instance.status


def test_rollback_error_is_detected(instance, monkeypatch):
    """"Every error during rollback should be detected and reported"""

    def raise_(*args, **kwargs):
        raise Exception('ABC')

    instance.github_repo_existed = False
    monkeypatch.setattr(instance.github, 'repo_exists', raise_)
    with pytest.raises(Exception, match='ABC'):
        instance.rollback()

    assert TaskExportProject.ROLLBACKED_ERROR in instance.status


def test_subtasks_are_added_to_subtask_list(instance, monkeypatch):
    """Successful export always consists of two tasks"""

    flexmock(TaskFetchGitlabProject, run=lambda: None)
    flexmock(TaskPushToGitHub, run=lambda: None)
    monkeypatch.setattr(instance.github, 'repo_exists', lambda x, y: False)
    instance.run()
    assert len(instance.subtasks) == 2
    assert TaskExportProject.SUCCESS in instance.status
