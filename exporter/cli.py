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


def load_all_gitlab_projects(gitlab):
    try:
        projects = gitlab.get_all_owned_projects()
        lines = list(map(lambda x: x['path'], projects))
        return ProjectLoader.load_parsed(lines)
    except Exception as e:
        raise click.BadParameter(e)


def load_config_file(ctx, param, value):
    try:
        cfg = configparser.ConfigParser()
        cfg.read_file(value)
        return ConfigLoader.load(cfg, value.name)
    except Exception as e:
        raise click.BadParameter(e)


def load_projects_file(ctx, param, value):
    try:
        if value is not None:
            return ProjectLoader.load(value)
        return None
    except Exception as e:
        raise click.BadParameter(e)


def delete_all_github_repos(ctx, param, value):
    if value:
        try:
            token = click.prompt('Enter GitHub token with admin access', hide_input=True)
            github = GitHubClient(token)
            repos = github.get_all_repos()
            if len(repos) == 0:
                print(f'There are no repositories to delete for login {github.login}.')
                return
            print(f'{len(repos)} repositories with login {github.login} will be deleted:'
                  f' {list(map(lambda x: x.get("name"), repos))}')
            if click.confirm('Do you really want to continue?'):
                for repo in repos:
                    repo_name, owner = repo['name'], repo['owner']['login']
                    github.delete_repo(repo_name, owner)
                    print(f'Repository {repo_name} deleted.')
        except HTTPError as e:
            print(e)
        finally:
            ctx.exit()


def validate_timeout(ctx, param, value):
    valid = True
    try:
        timeout = float(value)
        if timeout < 0 or timeout > 1000:
            valid = False
    except Exception:
        valid = False

    if not valid:
        raise click.BadParameter('Invalid timeout.')
    return timeout


# credit: Stephen Rauch, https://stackoverflow.com/a/51235564/6784881
class Mutex(click.Option):
    def __init__(self, *args, **kwargs):
        self.not_required_if = kwargs.pop("not_required_if")

        assert self.not_required_if, "'not_required_if' parameter required"
        kwargs["help"] = (kwargs.get("help", "") + " Option is mutually exclusive with " + ", ".join(
            self.not_required_if) + ".").strip()
        super(Mutex, self).__init__(*args, **kwargs)

    def handle_parse_result(self, ctx, opts, args):
        current_opt = self.name in opts
        for mutex_opt in self.not_required_if:
            if mutex_opt in opts:
                if current_opt:
                    raise click.UsageError(
                        "Illegal usage: '" + str(self.name) + "' is mutually exclusive with " + str(mutex_opt) + ".")
                else:
                    self.prompt = None
        return super(Mutex, self).handle_parse_result(ctx, opts, args)


@click.command(name='exporter')
@click.version_option(version='0.0.2')
@click.option('-c', '--config', type=click.File(mode='r'), callback=load_config_file,
              help='Exporter configuration file.', required=True)
@click.option('--export-all', is_flag=True, default=False, help='Export all GitLab projects.')
@click.option('-p', '--projects', type=click.File(mode='r', lazy=True), callback=load_projects_file,
              cls=Mutex, help='Project names to export. See Documentation for format.', not_required_if=['export-all'])
@click.option('--purge-gh', default=False, show_default=False, is_flag=True,
              is_eager=True, expose_value=False, callback=delete_all_github_repos,
              help='Prompt for GitHub token with admin access, delete all repos and exit. Dangerous!')
@click.option('--debug', default=False, is_flag=True,
              help='Enable debug logs.')
@click.option('--conflict-policy', type=click.Choice(['skip', 'overwrite', 'porcelain']),
              default='skip', help='If GitHub already contains repo with the same name as exported repo\n'
                                   '[skip]: do not export conflict repo and continue to the next one\n'
                                   '[overwrite]: overwrite conflict repo with exported repo\n'
                                   '[porcelain]: undo all export from progress from GitHub and end')
@click.option('--tmp-dir', type=click.Path(), help='Temporary directory to store exporting data.', default='tmp')
@click.option('--task-timeout', help='Floating point number specifying a timeout for the task.', default=10.0,
              callback=validate_timeout)
def main(config, projects, debug, conflict_policy, tmp_dir, task_timeout, export_all):
    """Tool for exporting projects from FIT CTU GitLab to GitHub"""
    gitlab = GitLabClient(token=config.gitlab_token)
    github = GitHubClient(token=config.github_token)

    if export_all:
        projects = load_all_gitlab_projects(gitlab)

    exporter = Exporter(
        gitlab=gitlab,
        github=github,
        logger=ExporterLogger(debug=debug),
        debug=debug
    )

    exporter.run(
        projects=projects,
        conflict_policy=conflict_policy,
        tmp_dir=tmp_dir,
        task_timeout=task_timeout
    )
