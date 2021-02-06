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

    @staticmethod
    def _parse_line(line):
        s = line.split(' ')
        if len(s) == 1 and len(s[0]):
            return s[0], s[0]
        elif len(s) == 3 and s[1] == '->' \
                and len(s[0]) and len(s[2]):
            return s[0], s[2]
        raise ValueError(f"Line '{line}'")

    @staticmethod
    def _check_unique_values(lines):
        dst = list(map(lambda x: x[1], lines))
        if len(dst) != len(set(dst)):
            raise ValueError("GitHub names must be unique.")

    @classmethod
    def load_parsed(cls, lines):
        lines_parsed = list(map(cls._parse_line, lines))
        cls._check_unique_values(lines_parsed)
        return lines_parsed

    @classmethod
    def load(cls, project_file):
        lines = [x.strip() for x in project_file.read().splitlines()]
        return cls.load_parsed(lines)
