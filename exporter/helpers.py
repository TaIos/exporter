import contextlib
import pathlib
import shutil

import click


@contextlib.contextmanager
def ensure_tmp_dir(path):
    path = path or 'tmp'
    p = pathlib.Path(path)
    if p.exists():
        if click.confirm(f"Tmp directory '{p.absolute()}' already exists.\nOverwrite it's content?"):
            shutil.rmtree(p)
        else:
            raise ValueError(
                f"Tmp directory '{p.absolute()}' already exists. Delete it or specify different directory.")
    p.mkdir()
    try:
        yield p
    finally:
        shutil.rmtree(p)
