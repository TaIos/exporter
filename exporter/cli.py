import click
import configparser

from exporter.logic import Exporter, GitLabClient, GitHubClient, TaskStream
from exporter.config import ConfigLoader, ProjectLoader


class ExporterLogger:

    def __init__(self, log_dir=None):
        self.log_dir = log_dir or 'logs'


def load_config_file(ctx, param, value):
    try:
        cfg = configparser.ConfigParser()
        cfg.read_file(value)
        return ConfigLoader.load(cfg, value.name)
    except Exception as e:
        raise click.BadParameter(f'Failed to load the configuration!')


def load_projects_file(ctx, param, value):
    try:
        return ProjectLoader.load(value)
    except Exception as e:
        raise click.BadParameter(f'Failed to load the projects file!')


@click.command(name='exporter')
@click.version_option(version='v0.0.0')
@click.option('-c', '--config', type=click.File(mode='r'), callback=load_config_file,
              help='Exporter configuration file.', required=True)
@click.option('-p', '--projects', type=click.File(mode='r'), callback=load_projects_file,
              help='Project names to export', required=True)
def main(config, projects):
    """An universal tool for exporting projects from FIT CTU GitLab to GitHub"""
    gitlab = GitLabClient(token=config.gitlab_token)
    github = GitHubClient(token=config.github_token)

    exporter = Exporter(
        gitlab=gitlab,
        github=github,
        logger=ExporterLogger()
    )

    exporter.run(
        projects=projects
    )
