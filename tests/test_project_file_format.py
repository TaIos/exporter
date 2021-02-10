import pytest

from helper import run_ok, run, dummy, projects


@pytest.fixture
def dummy_config_file():
    return 'dummy_config.cfg'


@pytest.mark.parametrize('projects_file', [
    'ok1_example.cfg',
    'ok2.cfg',
    'ok3.cfg',
    'ok4.cfg',
    'ok5.cfg',
    'ok6.cfg',
    'ok7.cfg',
])
def test_correct_project_files(projects_file, dummy_config_file):
    """"Application should accept this as input"""

    cp = run_ok(f'-p "{projects(projects_file)}" '
                f'-c "{dummy(dummy_config_file)}" '
                f'--dry-run')
    assert cp.returncode == 0
    assert not cp.stderr


def test_unique_github_names(dummy_config_file):
    """"Exporting two GitLab projects to one GitHub project doesn't make sense"""

    file = 'incorrect_ambiguous_github.cfg'
    cp = run(f'-p "{projects(file)}" '
             f'-c "{dummy(dummy_config_file)}" '
             f'--dry-run')
    assert cp.returncode != 0
    assert not cp.stdout
    assert (
            "Error: Invalid value for '-p' / '--projects': GitHub names must be unique." in cp.stderr
    )


def test_empty_file(dummy_config_file):
    """"Empty file is not allowed"""

    file = 'incorrect_empty.cfg'
    cp = run(f'-p "{projects(file)}" '
             f'-c "{dummy(dummy_config_file)}" '
             f'--dry-run')
    assert cp.returncode != 0
    assert not cp.stdout
    assert (
            "Error: Invalid value for '-p' / '--projects': File is empty." in cp.stderr
    )


def test_empty_line(dummy_config_file):
    """"Empty line is not allowed"""

    file = 'incorrect_empty_lines.cfg'
    cp = run(f'-p "{projects(file)}" '
             f'-c "{dummy(dummy_config_file)}" '
             f'--dry-run')
    assert cp.returncode != 0
    assert not cp.stdout
    assert (
            "Error: Invalid value for '-p' / '--projects': Empty line is not allowed." in cp.stderr
    )


def test_number_of_words_on_line(dummy_config_file):
    """"Number of entries separated by separator may not exceed certain limit"""

    file = 'incorrect_number_of_words.cfg'
    cp = run(f'-p "{projects(file)}" '
             f'-c "{dummy(dummy_config_file)}" '
             f'--dry-run')
    assert cp.returncode != 0
    assert not cp.stdout
    assert (
            "Error: Invalid value for '-p' / '--projects': Invalid number of entries on line" in cp.stderr
    )


def test_random_input(dummy_config_file):
    """"Random input should not be accepted"""

    file = 'incorrect_random.cfg'
    cp = run(f'-p "{projects(file)}" '
             f'-c "{dummy(dummy_config_file)}" '
             f'--dry-run')
    assert cp.returncode != 0
    assert not cp.stdout
    assert (
            "Error: Invalid value for '-p' / '--projects': Invalid number of entries on line" in cp.stderr
    )


@pytest.mark.parametrize('projects_file', [
    'incorrect_repo_separator_with_visibility.cfg',
    'incorrect_repo_separator_without_visibility.cfg',
])
def test_incorrect_repo_separator(projects_file, dummy_config_file):
    """"For renaming during export, special separator has to be used no matter the visibility."""

    cp = run(f'-p "{projects(projects_file)}" '
             f'-c "{dummy(dummy_config_file)}" '
             f'--dry-run')
    assert cp.returncode != 0
    assert not cp.stdout
    assert (
            "Error: Invalid value for '-p' / '--projects': Invalid separator" in cp.stderr
    )


@pytest.mark.parametrize('projects_file', [
    'incorrect_repo_visibility_specifier.cfg',
    'incorrect_repo_visibility_specifier_simple.cfg',
])
def test_incorrect_repo_separator(projects_file, dummy_config_file):
    """"Visibility specifier can only be from predefined discrete values"""

    cp = run(f'-p "{projects(projects_file)}" '
             f'-c "{dummy(dummy_config_file)}" '
             f'--dry-run')
    assert cp.returncode != 0
    assert not cp.stdout
    assert (
            "Error: Invalid value for '-p' / '--projects': Invalid visibility specifier" in cp.stderr
    )
