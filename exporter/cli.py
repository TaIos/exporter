import click
import configparser

from exporter.logic import Exporter, GitLabClient, GitHubClient, TaskStream
from exporter.config import ConfigLoader


class ExporterLogger:

    def __init__(self, log_dir=None):
        self.log_dir = log_dir or 'logs'


def load_config(ctx, param, value):
    try:
        cfg = configparser.ConfigParser()
        cfg.read_file(value)
        return ConfigLoader.load(cfg, value.name)
    except Exception as e:
        raise click.BadParameter(f'Failed to load the configuration!')


@click.command(name='exporter')
@click.version_option(version='v0.0.0')
@click.option('-c', '--config', type=click.File(mode='r'), callback=load_config,
              help='Exporter configuration file.', required=True)
def main(config):
    """An universal tool for exporting projects from FIT CTU GitLab to GitHub"""
    gitlab = GitLabClient(token=config.gitlab_token)
    github = GitHubClient(token=config.github_token)
    tasks = TaskStream()

    exporter = Exporter(
        gitlab=gitlab,
        github=github,
        logger=ExporterLogger()
    )

    exporter.run(
        task_stream=tasks
    )
