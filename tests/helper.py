import pathlib
import shlex
import subprocess
import sys

fixtures_dir = pathlib.Path(__file__).parent / 'fixtures'
configs_dir = fixtures_dir / 'config'
projects_dir = fixtures_dir / 'projects'
dummy_dir = fixtures_dir / 'dummy'


def config(name):
    return configs_dir / name


def projects(name):
    return projects_dir / name


def dummy(name):
    return dummy_dir / name


def run_ok(*args, **kwargs):
    cp = run(*args, **kwargs)
    print(cp.stdout, end='')
    print(cp.stderr, end='', file=sys.stderr)
    assert cp.returncode == 0
    assert not cp.stderr
    return cp


def run(line, entrypoint=False, **kwargs):
    if entrypoint:
        print('$ exporter', line)
        command = ['exporter']
    else:
        print('$ python -m exporter', line)
        command = [sys.executable, '-m', 'exporter']
    command = command + shlex.split(line)
    return subprocess.run(command,
                          stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE,
                          universal_newlines=True,
                          **kwargs)
