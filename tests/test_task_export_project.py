import pytest
from flexmock import flexmock

from exporter.logic import ProgressBarWrapper, TaskExportProject


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
        count=None
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


def test_if_run_is_skipped_when_repo_exists_and_policy_is_skip():
    """When conflict policy is set to 'skip' and GitHub project already exists, run should skipped"""
    ...


def test_if_overwrite_happens_when_repo_exists_and_policy_is_overwrite():
    """When conflict policy is set to 'overwrite' and GitHub project already exists, it should be overwritten"""
    ...


def test_if_rollback_deletes_repo_if_it_did_not_existed_before():
    """Rollback should undone everything, including deleting created GitHub repository if it did not existed before"""
    ...


def test_if_rollback_doesnt_delete_repo_if_it_existed_before():
    """Rollback should undone everything, but not delete created GitHub repository if it did existed before"""
    ...


def test_rollback_error_is_detected():
    """"Every error during rollback should be detected and reported"""
    ...


def test_subtasks_are_added_to_subtask_list():
    """Successfull export always consists of two tasks"""
    ...
