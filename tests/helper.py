import pathlib
import shlex
import subprocess
import sys

fixtures_dir = pathlib.Path(__file__).parent / 'fixtures'


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
