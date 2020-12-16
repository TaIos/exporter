import pathlib


class SimpleGitWrapper:

    def __init__(self, project_dir):
        self.project_dir = pathlib.Path(project_dir).resolve()
