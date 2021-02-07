import random
import pathlib
import shutil
import string

import click


def rndstr(length):
    return ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(length))


def ensure_tmp_dir(path):
    p = pathlib.Path(path)
    if p.exists():
        if click.confirm(f"Tmp directory '{p.absolute()}' already exists.\nOverwrite it's content?"):
            shutil.rmtree(p)
        else:
            raise click.ClickException(
                f"Tmp directory '{p.absolute()}' already exists. Delete it or specify different directory.")
    p.mkdir()
    return p


# credit to Carl F.:  https://stackoverflow.com/a/8290508/6784881
def split_to_batches(iterable, n=1):
    l = len(iterable)
    for ndx in range(0, l, n):
        yield iterable[ndx:min(ndx + n, l)]


def flatten(t):
    flat_list = []
    for sublist in t:
        for item in sublist:
            flat_list.append(item)
    return flat_list
