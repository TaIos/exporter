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


class LineParser:

    @classmethod
    def parse(cls, line):
        s = line.split(' ')
        if len(s) == 1:
            return cls._parse_line_with_split_len_1(s)
        elif len(s) == 2:
            return cls._parse_line_with_split_len_2(s)
        elif len(s) == 3:
            return cls._parse_line_with_split_len_3(s)
        elif len(s) == 4:
            return cls._parse_line_with_split_len_4(s)
        else:
            raise ValueError(f"Invalid number of entries on line '{line}'")

    @staticmethod
    def _parse_line_with_split_len_1(s):
        if len(s[0]):
            return [s[0], s[0]]
        if len(s[0]) == 0:
            raise ValueError(f"Empty line is not allowed.")
        raise ValueError()

    @staticmethod
    def _parse_line_with_split_len_2(s):
        if s[1] not in ['public', 'private']:
            raise ValueError(f"Invalid visibility specifier '{s[1]}'")
        if s[0]:
            return [s[0], s[0], s[1]]
        raise ValueError()

    @staticmethod
    def _parse_line_with_split_len_3(s):
        if s[1] != '->':
            raise ValueError(f"Invalid separator '{s[1]}'")
        if len(s[0]) and len(s[2]):
            return [s[0], s[2]]
        raise ValueError()

    @staticmethod
    def _parse_line_with_split_len_4(s):
        a, b, = LineParser._parse_line_with_split_len_3(s[:3])
        c = s[3]
        if c in ['private', 'public']:
            return [a, b, c]
        else:
            raise ValueError(f"Invalid visibility specifier '{c}'")


class ProjectLoader:

    @staticmethod
    def _check_unique_values(lines):
        dst = list(map(lambda x: x[1], lines))
        if len(dst) != len(set(dst)):
            raise ValueError("GitHub names must be unique.")

    @classmethod
    def load_parsed(cls, lines):
        lines_parsed = list(map(LineParser.parse, lines))
        cls._check_unique_values(lines_parsed)
        return lines_parsed

    @classmethod
    def load(cls, project_file):
        lines = [x.strip() for x in project_file.read().splitlines()]
        if len(lines) == 0:
            raise ValueError("File is empty.")
        return cls.load_parsed(lines)


class ProjectNormalizer:
    @classmethod
    def normalize(cls, projects, visibility):
        for i, p in enumerate(projects):
            if len(p) == 1:
                projects[i] = [p[0], p[0], visibility]
            elif len(p) == 2:
                projects[i] = [p[0], p[1], visibility]
            elif len(p) == 3:
                pass
            else:
                raise ValueError(f"Line '{p}'")
