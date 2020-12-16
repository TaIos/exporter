import contextlib
import pathlib
import shutil


@contextlib.contextmanager
def ensure_tmp_dir(path):
    path = path or 'tmp'
    pathlib.Path(path).mkdir()
    try:
        yield pathlib.Path(path).resolve()
    finally:
        shutil.rmtree(path)
