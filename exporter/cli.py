import click
import configparser
import logging
import pathlib
import time
from requests import HTTPError

from .logic import Exporter, GitLabClient, GitHubClient
from .config import ConfigLoader, ProjectLoader


class ExporterLogger:

    def __init__(self, debug=False, log_dir=None):
        self.log_dir = pathlib.Path(log_dir or 'logs')
        self.log_dir.mkdir(exist_ok=True, parents=True)
        self.level = logging.DEBUG if debug else logging.INFO
        logging.basicConfig(filename=(self.log_dir / time.strftime("%d%m%Y_%H%M%S")).with_suffix(".log"),
                            filemode='w',
                            level=self.level,
                            format='%(asctime)s: %(message)s',
                            datefmt='%d-%m-%Y %H:%M:%S %Z %z')

    def info(self, msg):
        logging.info(msg)


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


def delete_all_github_repos(ctx, param, value):
    if value:
        try:
            if click.confirm('Do you really want to delete all github repos?'):
                token = click.prompt('Enter GitHub token', hide_input=True)
                github = GitHubClient(token)
                for repo in github.get_all_repos():
                    repo_name, owner = repo['name'], repo['owner']['login']
                    github.delete_repo(repo_name, owner)
                    print(f'Repository {repo_name} deleted.')
        except HTTPError as e:
            print(e)
        finally:
            ctx.exit()


@click.command(name='exporter')
@click.version_option(version='0.0.1')
@click.option('-c', '--config', type=click.File(mode='r'), callback=load_config_file,
              help='Exporter configuration file.', required=True)
@click.option('-p', '--projects', type=click.File(mode='r'), callback=load_projects_file,
              help='Project names to export', required=True)
@click.option('-f', '--force', default=False, show_default=True, is_flag=True,
              help='Overwrite existing directories.')
@click.option('--purge-gh', default=False, show_default=True, is_flag=True,
              is_eager=True, expose_value=False, callback=delete_all_github_repos,
              help='Dangerous, this deletes all GitHub repos!')
@click.option('--debug', default=False, is_flag=True,
              help='Enable debug logs.')
def main(config, projects, force, debug):
    """Tool for exporting projects from FIT CTU GitLab to GitHub"""
    gitlab = GitLabClient(token=config.gitlab_token)
    github = GitHubClient(token=config.github_token)

    exporter = Exporter(
        gitlab=gitlab,
        github=github,
        logger=ExporterLogger(debug=debug)
    )

    exporter.run(
        projects=projects,
        force_overwrite=force
    )
