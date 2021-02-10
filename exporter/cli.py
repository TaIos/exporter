import click
import configparser

from requests import HTTPError

from .helpers import rndstr
from .logger import ExporterLogger
from .logic import Exporter, GitLabClient, GitHubClient
from .config import ConfigLoader, ProjectLoader, ProjectNormalizer


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
        return ConfigLoader.load(cfg)
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
        if timeout < 1 or timeout > 60:
            valid = False
    except Exception:
        valid = False

    if not valid:
        raise click.BadParameter('Invalid timeout.')
    return timeout


def make_unique_projects(projects, random_suffix_length):
    """Add random suffix to given project names"""
    for p in projects:
        p[1] = p[1] + '_' + rndstr(random_suffix_length)


def normalize_projects(projects, visibility):
    try:
        ProjectNormalizer.normalize(projects, visibility)
    except Exception as e:
        raise click.BadParameter(e)


class Mutex(click.Option):
    """Used for creating mutual exclusive options inside click.
    Credit `Stephen Rauch <https://stackoverflow.com/a/51235564/6784881>`_"""

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


def validate_batch_size(ctx, param, value):
    if value < 1:
        raise click.BadParameter('Invalid batch size.')
    return value


@click.command(name='exporter')
@click.version_option(version='1.0.0')
@click.option('-c', '--config', type=click.File(mode='r'), callback=load_config_file,
              help='File containing GitHub and GitLab tokens.', required=True)
@click.option('--export-all', is_flag=True, default=False,
              help='Export all GitLab projects associated with given token.')
@click.option('-p', '--projects', type=click.File(mode='r', lazy=True), callback=load_projects_file,
              cls=Mutex, help='Project names to export. See Documentation for format.', not_required_if=['export-all'])
@click.option('--purge-gh', default=False, show_default=False, is_flag=True,
              is_eager=True, expose_value=False, callback=delete_all_github_repos,
              help='Prompt for GitHub token with admin access, delete all repos and exit. Dangerous!')
@click.option('--debug', default=False, is_flag=True,
              help='Run application in debug mode. Application is unstable in this mode.')
@click.option('--conflict-policy', type=click.Choice(['skip', 'overwrite']),
              default='skip', help='[skip] skip export for project names which already exists on GitHib.'
                                   '[overwrite] overwrite any GitHub project which already exists.')
@click.option('--tmp-dir', type=click.Path(), help='Temporary directory to store data during export.',
              default='tmp', show_default=True)
@click.option('--task-timeout', help='Timeout for unresponding export task.',
              default=30.0, callback=validate_timeout, show_default=True)
@click.option('--unique', is_flag=True, default=False,
              help='Prevent GitHub name conflicts by appending random string at the end of exported project name.')
@click.option('--visibility', default='private', show_default=True, type=click.Choice(['public', 'private']),
              help='Visibility of the exported project on GitHub')
@click.option('--batch-size', default=10, show_default=True, callback=validate_batch_size,
              help='Maximum count of simultaneously running tasks.')
@click.option('--dry-run', default=False, is_flag=True,
              help='Do not perform any changes on GitLab and Github.')
def main(config, projects, debug, conflict_policy, tmp_dir, task_timeout, export_all, unique, visibility,
         batch_size, dry_run):
    """Tool for exporting projects from FIT CTU GitLab to GitHub"""
    gitlab = GitLabClient(token=config.gitlab_token)
    github = GitHubClient(token=config.github_token)

    if export_all:
        projects = load_all_gitlab_projects(gitlab)
    if unique:
        make_unique_projects(projects, random_suffix_length=6)

    normalize_projects(projects, visibility)

    exporter = Exporter(
        gitlab=gitlab,
        github=github,
        logger=ExporterLogger(),
        debug=debug
    )

    exporter.run(
        projects=projects,
        conflict_policy=conflict_policy,
        tmp_dir=tmp_dir,
        task_timeout=task_timeout,
        batch_size=batch_size,
        dry_run=dry_run
    )
