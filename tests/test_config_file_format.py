import pytest

from helper import run_ok, run, dummy, config


@pytest.fixture
def dummy_project_file():
    return 'dummy_projects.cfg'


@pytest.mark.parametrize('config_file', [
    'ok_additional_sections.cfg',
    'ok_example_config.cfg'
])
def test_correct_config_file(config_file, dummy_project_file):
    """"Application should accept this as input"""

    cp = run_ok(f'-p "{dummy(dummy_project_file)}" '
                f'-c "{config(config_file)}" '
                f'--dry-run')
    assert cp.returncode == 0
    assert not cp.stderr


def test_missing_github_section(dummy_project_file):
    """"Config file must contain github section"""

    config_file = 'missing_github_section.cfg'
    cp = run(f'-p "{dummy(dummy_project_file)}" '
             f'-c "{config(config_file)}" '
             f'--dry-run')
    assert cp.returncode != 0
    assert not cp.stdout
    assert (
            "Error: Invalid value for '-c' / '--config': No section: 'github'" in cp.stderr
    )


def test_missing_gitlab_section(dummy_project_file):
    """"Config file must contain gitlab section"""

    config_file = 'missing_gitlab_section.cfg'
    cp = run(f'-p "{dummy(dummy_project_file)}" '
             f'-c "{config(config_file)}" '
             f'--dry-run')
    assert cp.returncode != 0
    assert not cp.stdout
    assert (
            "Error: Invalid value for '-c' / '--config': No section: 'gitlab'" in cp.stderr
    )


def test_missing_github_and_gitlab_section(dummy_project_file):
    """"Config file must contain both github and gitlab this section"""

    config_file = 'missing_github_and_gitlab_section.cfg'
    cp = run(f'-p "{dummy(dummy_project_file)}" '
             f'-c "{config(config_file)}" '
             f'--dry-run')
    assert cp.returncode != 0
    assert not cp.stdout
    assert (
            "Error: Invalid value for '-c' / '--config': No section: 'github' and 'gitlab'" in cp.stderr
    )


def test_missing_github_token(dummy_project_file):

    """"Config file must contain github token"""
    config_file = 'missing_github_token.cfg'
    cp = run(f'-p "{dummy(dummy_project_file)}" '
             f'-c "{config(config_file)}" '
             f'--dry-run')
    assert cp.returncode != 0
    assert not cp.stdout
    assert (
            "Error: Invalid value for '-c' / '--config': No 'token' in section 'github'" in cp.stderr
    )


def test_missing_gitlab_token(dummy_project_file):
    """"Config file must contain gitlab token"""

    config_file = 'missing_gitlab_token.cfg'
    cp = run(f'-p "{dummy(dummy_project_file)}" '
             f'-c "{config(config_file)}" '
             f'--dry-run')
    assert cp.returncode != 0
    assert not cp.stdout
    assert (
            "Error: Invalid value for '-c' / '--config': No 'token' in section 'gitlab'" in cp.stderr
    )


def test_empty_config_file(dummy_project_file):
    """"Empty config is invalid"""

    config_file = 'empty_config.cfg'
    cp = run(f'-p "{dummy(dummy_project_file)}" '
             f'-c "{config(config_file)}" '
             f'--dry-run')
    assert cp.returncode != 0
    assert not cp.stdout
    assert (
            "Error: Invalid value for '-c' / '--config': No section: 'github' and 'gitlab'" in cp.stderr
    )
