import pathlib


class ExporterConfig:

    def __init__(self, github_token, gitlab_token):
        self.github_token = github_token
        self.gitlab_token = gitlab_token


class ConfigLoader:

    @classmethod
    def load(cls, cfg, config_file):
        config_dir = pathlib.Path(config_file).resolve().parents[0]
        config = ExporterConfig(
            github_token=cfg.get('github', 'token'),
            gitlab_token=cfg.get('gitlab', 'token'),
        )
        return config


class ProjectLoader:

    @classmethod
    def load(cls, project_file):
        return [x.strip() for x in project_file.read().splitlines()]
