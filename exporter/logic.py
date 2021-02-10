import click
import requests
import re
import shutil
import uuid
import git  # documentation: https://gitpython.readthedocs.io/en/stable/reference.html
import enlighten

from threading import Thread
from abc import ABC

from .exeptions import MultipleGitLabProjectsExistException, NoGitLabProjectsExistException
from .helpers import ensure_tmp_dir, rndstr, split_to_batches, flatten


class GitHubClient:
    """
    This class can communicate with the GitHub API.
    Just give it a token and go.

    Github API `documentation <https://docs.github.com/en/free-pro-team@latest/rest/reference>`__
    """
    API = 'https://api.github.com'

    def __init__(self, token, session=None):
        self.token = token
        self.session = session or requests.Session()
        self.session.headers = {'User-Agent': 'exporter'}
        self.session.auth = self._token_auth
        self._login = None

    def clone(self):
        """Create deep copy"""
        return GitHubClient(self.token)

    @property
    def login(self):
        """Return user login name associated with token"""
        if self._login is None:
            self._login = self.user().get('login')
        return self._login

    def _token_auth(self, req):
        req.headers['Authorization'] = 'token ' + self.token
        return req

    def _paginated_json_get(self, url, params=None):
        r = self.session.get(url=url, params=params)
        r.raise_for_status()
        json = r.json()
        if 'next' in r.links and 'url' in r.links['next']:
            json += self._paginated_json_get(r.links['next']['url'], params)
        return json

    def _post(self, url, json=None):
        r = self.session.post(url=url, json=json)
        r.raise_for_status()

    def _delete(self, url):
        r = self.session.delete(url=url)
        r.raise_for_status()

    def user(self):
        """Return all user information"""
        return self._paginated_json_get(f'{self.API}/user')

    def get_all_repos(self):
        return self._paginated_json_get(f'{self.API}/user/repos')

    def delete_repo(self, repo_name, owner):
        self._delete(f'{self.API}/repos/{owner}/{repo_name}')

    def repo_exists(self, repo_name, owner):
        return self.session.get(url=f'{self.API}/repos/{owner}/{repo_name}').status_code == 200

    def create_repo(self, repo_name, data=None, is_private=None):
        data = data or dict()
        data['name'] = repo_name
        data['private'] = is_private
        self._post(f'{self.API}/user/repos', data)


class GitLabClient:
    """
    This class can communicate with the GitLab API.
    just give it a token and go.

    GitLab API `documentation <https://gitlab.fit.cvut.cz/help/api/README.md>`_
    """
    API = 'https://gitlab.fit.cvut.cz/api/v4'

    def __init__(self, token, session=None):
        self.token = token
        self.session = session or requests.Session()
        self.session.headers = {'User-Agent': 'exporter'}
        self.session.auth = self._token_auth

    def clone(self):
        return GitLabClient(self.token)

    def _token_auth(self, req):
        req.headers['Private-Token'] = self.token
        return req

    def _paginated_json_get(self, url, params=None):
        r = self.session.get(url=url, params=params)
        r.raise_for_status()
        json = r.json()
        if 'next' in r.links and 'url' in r.links['next']:
            json += self._paginated_json_get(r.links['next']['url'], params)
        return json

    def user(self):
        return self._paginated_json_get(f'{self.API}/user')

    def get_all_owned_projects(self):
        return self._paginated_json_get(f'{self.API}/projects', params={'owned': True})

    def search_owned_projects(self, search):
        return self._paginated_json_get(f'{self.API}/projects', params={'owned': True, 'search': search})


class TaskBase(ABC):
    """
    Abstract class representing runnable task inside Exporter application.
    """

    def __init__(self):
        self.id = str(uuid.uuid4())  # make a random UUID
        self.running = False
        self.exc = []  # list of caught exceptions during execution
        self.subtasks = []  # list of subtasks used by this task
        self.suppress_exceptions = False  # if false suppress any exception throwing
        self.status = set()

    def run(self):
        """Start task"""
        pass

    def stop(self):
        """Stop task"""
        self.running = False
        for task in self.subtasks:
            task.stop()

    def raise_if_not_running(self):
        """Raise exception if task is not running"""
        if not self.running:
            raise InterruptedError(self.id)

    def rollback(self):
        """Undo everything that this task has done"""
        for task in self.subtasks:
            task.rollback()


class TaskFetchGitlabProject(TaskBase):
    """Task that fetches specified GitLab project"""

    def __init__(self, gitlab, name_gitlab, base_dir, bar, suppress_exceptions, debug):
        super().__init__()
        self.gitlab = gitlab
        self.name_gitlab = name_gitlab
        self.base_dir = base_dir
        self.bar = bar
        self.suppress_exceptions = suppress_exceptions
        self.id = name_gitlab
        self.debug = debug

    def run(self):
        """
        Fetch specified GitLab project

        :return: :class:`git.Repo` instance pointing to the cloned project
        """
        try:
            self.running = True
            self.bar.set_msg('Searching for project')
            r = self.gitlab.search_owned_projects(self.name_gitlab)
            self.bar.set_msg_and_update('Searching for project done')
            if len(r) > 1:
                raise MultipleGitLabProjectsExistException(f'Multiple projects found for {self.name_gitlab}')
            if len(r) == 0:
                raise NoGitLabProjectsExistException(f'No project found for {self.name_gitlab}')
            json = r[0]

            username = json['owner']['username']
            password = self.gitlab.token
            url = json['http_url_to_repo']
            auth_https_url = re.sub(r'(https://)', f'\\1{username}:{password}@', url)
            self.raise_if_not_running()
            self.bar.set_msg('Cloning GitLab repo')
            git_cmd = git.Repo.clone_from(auth_https_url, self.base_dir / (self.name_gitlab + rndstr(5)))
            self.raise_if_not_running()
            self.bar.set_msg_and_update('Fetching GitLab LFS files')
            git.cmd.Git(working_dir=git_cmd.working_dir).execute(['git', 'lfs', 'fetch', '--all'])
            self.bar.set_msg_and_update('Fetching GitLab LFS files done')
            self.running = False
            return git_cmd
        except Exception as e:
            self.running = False
            self.exc.append(e)
            if self.debug:
                click.secho(f'ERROR in {self.id}: {e}', fg='red', bold=True)
            if not self.suppress_exceptions:
                raise


class TaskPushToGitHub(TaskBase):
    """Task that pushes specified fetched GitLab project to GitHub"""

    def __init__(self, github, git_cmd, name_github, is_private, bar, suppress_exceptions, debug):
        super().__init__()
        self.github = github
        self.git_cmd = git_cmd
        self.name_github = name_github
        self.is_private = is_private
        self.bar = bar
        self.id = name_github
        self.suppress_exceptions = suppress_exceptions
        self.debug = debug

    def run(self):
        """
        Push specified fetched GitLab project to GitHub

        :return: None
        """
        try:
            self.running = True
            self.bar.set_msg('Creating GitHub repo')
            self.github.create_repo(repo_name=self.name_github, is_private=self.is_private)
            self.bar.update()
            owner = self.github.login
            password = self.github.token
            auth_https_url = f'https://{owner}:{password}@github.com/{owner}/{self.name_github}.git'
            self.raise_if_not_running()
            remote = self.git_cmd.create_remote(f'github_{self.name_github}', auth_https_url)
            self.raise_if_not_running()
            self.bar.set_msg('Pushing to GitHub')
            if int(self.git_cmd.git.rev_list('--all', '--count')) >= 1:  # no commits, git can't push
                remote.push()
            self.bar.set_msg_and_update('Pushing to GitHub done')
            self.running = False
        except Exception as e:
            self.running = False
            self.exc.append(e)
            if self.debug:
                click.secho(f'ERROR in {self.id}: {e}', fg='red', bold=True)
            if not self.suppress_exceptions:
                raise


class TaskExportProject(TaskBase):
    """
    Task that exports specifies GitLab project to GitHub
    """

    """Status constants indicating encountered events during :func:`run` and :func:`rollback`"""
    SKIPPED = 'SKIPPED'
    OVERWRITTEN = 'OVERWRITTEN'
    FETCHED = 'FETCHED'
    SUCCESS = 'SUCCESS'
    INTERRUPTED = 'INTERRUPTED'
    ERROR = 'ERROR'
    ROLLBACKED = 'ROLLBACKED'
    ROLLBACKED_ERROR = 'ROLLBACKED_ERROR'
    DRY_RUN = 'DRY_RUN'
    MULTIPLE_GITLAB_PROJECTS = 'MULTIPLE_GITLAB_PROJECTS'
    NO_GITLAB_PROJECT = 'NO_GITLAB_PROJECT'

    def __init__(self, gitlab, github, name_gitlab, name_github, is_github_private,
                 base_dir, bar, conflict_policy, suppress_exceptions, debug):
        super().__init__()
        self.gitlab = gitlab
        self.github = github
        self.name_gitlab = name_gitlab
        self.name_github = name_github
        self.is_github_private = is_github_private
        self.base_dir = base_dir
        self.bar = bar
        self.conflict_policy = conflict_policy
        self.id = f'{name_gitlab}->{name_github}'
        self.suppress_exceptions = suppress_exceptions
        self.github_repo_existed = None
        self.debug = debug
        self.status = set()

    def run(self):
        """
        Export specified GitLab project to GitHub

        :return: None
        """
        try:
            self.running = True
            self.github_repo_existed = self.github.repo_exists(self.name_github, self.github.login)
            if self.github_repo_existed:
                if self.conflict_policy == 'skip':
                    self.bar.set_msg_and_finish('SKIPPED')
                    self.status.add(self.SKIPPED)
                    self.running = False
                    return
                elif self.conflict_policy in ['overwrite']:
                    self.bar.set_msg('Deleting GitHubProject')
                    self.github.delete_repo(self.name_github, self.github.login)
                    self.bar.set_msg('GitHub project deleted')
                    self.status.add(self.OVERWRITTEN)

            task_fetch_gitlab_project = TaskFetchGitlabProject(
                gitlab=self.gitlab,
                name_gitlab=self.name_gitlab,
                base_dir=self.base_dir,
                bar=self.bar,
                suppress_exceptions=False,
                debug=self.debug
            )
            self.subtasks.append(task_fetch_gitlab_project)
            self.raise_if_not_running()
            self.bar.set_msg('Starting fetching GitLab project')
            git_cmd = task_fetch_gitlab_project.run()
            self.bar.set_msg('Fetching GitLab project done')
            self.status.add(self.FETCHED)

            task_push_to_github = TaskPushToGitHub(
                github=self.github,
                git_cmd=git_cmd,
                name_github=self.name_github,
                is_private=self.is_github_private,
                bar=self.bar,
                suppress_exceptions=False,
                debug=self.debug
            )
            self.subtasks.append(task_push_to_github)
            self.raise_if_not_running()
            self.bar.set_msg('Starting pushing to GitHub')
            task_push_to_github.run()
            self.bar.set_msg_and_finish('DONE')
            self.status.add(self.SUCCESS)
            self.running = False
        except (InterruptedError, KeyboardInterrupt):
            self.running = False
            self.bar.set_msg_and_finish('INTERRUPTED')
            self.status.add(self.INTERRUPTED)
        except NoGitLabProjectsExistException as e:
            self.running = False
            self.bar.set_msg_and_finish('NO GITLAB PROJECT')
            self.status.add(self.NO_GITLAB_PROJECT)
        except MultipleGitLabProjectsExistException as e:
            self.running = False
            self.bar.set_msg_and_finish('MULTIPLE GITLAB PROJECTS')
            self.status.add(self.MULTIPLE_GITLAB_PROJECTS)
        except Exception as e:
            self.running = False
            self.exc.append(e)
            self.bar.set_msg_and_finish('RUN ERROR')
            self.status.add(self.ERROR)
            if self.debug:
                click.secho(f'ERROR in {self.id}: {e}', fg='red', bold=True)
            if not self.suppress_exceptions:
                raise

    def rollback(self):
        """Undo everything that export process has done. This includes deleting GitHub repository
        if it did not existed before export and has been created in :func:`run` method"""
        try:
            if not self.github_repo_existed and self.github.repo_exists(self.name_github, self.github.login):
                self.github.delete_repo(self.name_github, self.github.login)
            self.bar.set_msg('ROLLBACKED')
            self.status.add(self.ROLLBACKED)
        except Exception as e:
            self.bar.set_msg('ROLLBACK ERROR')
            self.status.add(self.ROLLBACKED_ERROR)
            if self.debug:
                click.secho(f'ERROR in {self.id}: {e}', fg='red', bold=True)
            raise


class ProgressBarWrapper:
    """Progress bar wrapper API that informs user about export progress"""

    def __init__(self, bar, initial_message):
        self.bar = bar
        self.set_msg(initial_message)

    def update(self):
        self.bar.update()
        self.refresh()

    def set_msg(self, msg):
        self.bar.unit = msg
        self.refresh()

    def set_msg_and_update(self, msg):
        self.set_msg(msg)
        self.update()

    def set_msg_and_finish(self, msg):
        self.set_msg(msg)
        self.set_finished()

    def set_finished(self):
        self.bar.count = self.bar.total
        self.refresh()

    def is_finished(self):
        return self.bar.count == self.bar.total

    def refresh(self):
        self.bar.refresh()

    def close(self):
        self.bar.close()


class TaskProgressBarPool(TaskBase):
    """
    Used bar implementation `documentation <https://python-enlighten.readthedocs.io/en/stable/api.html>`__
    """

    ID = 'PROGRESS_BAR'

    def __init__(self):
        super().__init__()
        self.pool = []
        self.manager = enlighten.get_manager()
        self.bar_format = '{desc}{desc_pad}{percentage:3.0f}%|{bar}| {count:{len_total}d}/{total:d} [{unit}]'
        self.id = TaskProgressBarPool.ID

    def register(self, name, total, initial_message):
        """
        Create new progress bar, add it to pool and return its API

        :param name: string to display as the name of the progress bar
        :param total: total ticks of the progress bar (eg 100)
        :param initial_message: string to display as the current state of the progress bar
        :return: :class:`ProgressBarWrapper` as the progress bar API
        """
        bar = self.manager.counter(
            total=total,
            desc=name,
            unit="ticks",
            color="red",
            bar_format=self.bar_format,
            autorefresh=False,
            threaded=True,
            no_resize=False
        )
        bar_wrapper = ProgressBarWrapper(bar, initial_message=initial_message)
        self.pool.append(bar_wrapper)
        return bar_wrapper

    def refresh(self):
        """Redraw all progress bars in pool"""
        for bar in self.pool:
            bar.refresh()

    def run(self):
        """
        Start redrawing all progress bars inside pool until :attr:`running` flag is true or any progress
        bar is not finished
        """
        self.running = True
        while not all([x.is_finished() for x in self.pool]) and self.running:
            self.refresh()
        for bar in self.pool:
            bar.close()
        try:
            self.manager.stop()
        except Exception:
            pass


class Exporter:

    def __init__(self, gitlab, github, logger, debug):
        self.github = github
        self.gitlab = gitlab
        self.logger = logger
        self.debug = debug

    def run(self, projects, conflict_policy, tmp_dir, task_timeout, batch_size, dry_run):
        """
        Start export of specified projects from GitLab to GitHub.
        Run at most :attr:`batch_size` project exports in parallel.
        """
        tasks_batched = []
        running_threads = []
        runned_tasks = []
        tmp_dir = ensure_tmp_dir(tmp_dir)
        try:
            tasks_batched = self._prepare_batched_tasks(
                gitlab=self.gitlab,
                github=self.github,
                projects=projects,
                batch_size=batch_size,
                tmp_dir=tmp_dir,
                conflict_policy=conflict_policy,
                debug=self.debug,
                suppress_exceptions=not self.debug
            )
            for tasks in tasks_batched:
                running_threads = []
                runned_tasks += tasks
                self._execute_tasks(
                    tasks=tasks,
                    threads=running_threads,
                    dry_run=dry_run
                )
        except KeyboardInterrupt:
            self._handle_keyboard_interrupt(runned_tasks, running_threads, task_timeout)
        except Exception as e:
            self._handle_generic_exception(runned_tasks, running_threads, task_timeout, e)
        finally:
            ExporterPrinter(logger=self.logger).report(
                tasks=flatten(tasks_batched),
                runned_tasks=runned_tasks
            )
            shutil.rmtree(tmp_dir)

    @staticmethod
    def _prepare_batched_tasks(gitlab, github, projects, tmp_dir, conflict_policy, debug,
                               suppress_exceptions, batch_size):
        batched_tasks = []
        for batch in split_to_batches(projects, batch_size):
            batched_tasks.append(
                Exporter._prepare_tasks(gitlab=gitlab,
                                        github=github,
                                        projects=batch,
                                        tmp_dir=tmp_dir,
                                        conflict_policy=conflict_policy,
                                        debug=debug,
                                        suppress_exceptions=suppress_exceptions
                                        ))
        return batched_tasks

    @staticmethod
    def _prepare_tasks(gitlab, github, projects, tmp_dir, conflict_policy, debug, suppress_exceptions):
        tasks = []
        bar_task = TaskProgressBarPool()
        for name_gitlab, name_github, visibility_github in projects:
            bar = bar_task.register(
                name=f'[{name_gitlab}]' if name_gitlab == name_github else f'[{name_gitlab} -> {name_github}]',
                total=5,
                initial_message='WAITING'
            )
            tasks.append(TaskExportProject(
                gitlab=gitlab.clone(),
                github=github.clone(),
                name_gitlab=name_gitlab,
                name_github=name_github,
                is_github_private=visibility_github == 'private',
                base_dir=tmp_dir,
                bar=bar,
                conflict_policy=conflict_policy,
                suppress_exceptions=suppress_exceptions,
                debug=debug
            ))
        tasks.append(bar_task)
        return tasks

    @staticmethod
    def _execute_tasks(tasks, threads, dry_run):
        if dry_run:
            for task in tasks:
                task.status.add(TaskExportProject.DRY_RUN)
            return

        for task in tasks:
            t = Thread(target=task.run, args=())
            t.start()
            threads.append(t)
        for t in threads:
            t.join()

    @staticmethod
    def _rollback(tasks, debug):
        for task in tasks:
            try:
                task.rollback()
            except Exception as e:
                if debug:
                    click.secho(f'{e}', fg='red', bold=True)

    @staticmethod
    def _stop_execution(tasks, threads, task_timeout):
        for task in tasks:
            task.stop()
        for t in threads:
            t.join(task_timeout)

    def _handle_keyboard_interrupt(self, tasks, threads, task_timeout):
        click.secho(f'===STOPPING===', bold=True)
        self._stop_execution(tasks=tasks, threads=threads, task_timeout=task_timeout)
        self._rollback(tasks=tasks, debug=self.debug)

    def _handle_generic_exception(self, tasks, threads, task_timeout, exception):
        click.secho(f'ERROR: {exception}', fg='red', bold=True)
        self._stop_execution(tasks=tasks, threads=threads, task_timeout=task_timeout)
        self._rollback(tasks=tasks, debug=self.debug)
        if self.debug:
            raise


class ExporterPrinter:

    def __init__(self, logger):
        self.logger = logger

    def print_project_name(self, name):
        click.secho(f'{name}', bold=True)

    def _prefix_result(self):
        click.secho(' => ', bold=True, nl=False)

    def report(self, tasks, runned_tasks):
        runned_id = set(map(lambda x: x.id, runned_tasks))
        for t in tasks:
            self._dump_to_logfile(t)

            if t.id == TaskProgressBarPool.ID:
                continue

            self.print_project_name(t.id)
            self._prefix_result()

            if t.id not in runned_id:
                self._not_runned()
            if TaskExportProject.SUCCESS in t.status:
                self._success()
            if TaskExportProject.OVERWRITTEN in t.status:
                self._overwritten()
            if TaskExportProject.ERROR in t.status:
                self._run_error()
            if TaskExportProject.INTERRUPTED in t.status:
                self._interrupted()
            if TaskExportProject.SKIPPED in t.status:
                self._skipped()
            if TaskExportProject.ROLLBACKED in t.status:
                self._rollback()
            if TaskExportProject.ROLLBACKED_ERROR in t.status:
                self._rollback_error()
            if TaskExportProject.DRY_RUN in t.status:
                self._dry_run()
            if TaskExportProject.NO_GITLAB_PROJECT in t.status:
                self._no_gitlab_project()
            if TaskExportProject.MULTIPLE_GITLAB_PROJECTS in t.status:
                self._multiple_gitlab_projects()
            click.secho('', )

    def _dump_to_logfile(self, task):
        sta_to_str = ':'.join(map(str, task.status))
        exc_to_str = '-'.join(map(str, task.exc))
        self.logger.info(f'{task.id} {sta_to_str} {exc_to_str}')

    @staticmethod
    def _success():
        click.secho('EXPORTED ', fg='green', nl=False)

    @staticmethod
    def _skipped():
        click.secho('SKIPPED ', fg='yellow', nl=False)

    @staticmethod
    def _rollback():
        click.secho('SUCCESS_ROLLBACK ', fg='green', nl=False)

    @staticmethod
    def _rollback_error():
        click.secho('ERROR_ROLLBACK ', fg='red', nl=False)

    @staticmethod
    def _run_error():
        click.secho('RUN_ERROR ', fg='red', nl=False)

    @staticmethod
    def _not_runned():
        click.secho('NOT_RUNNED ', fg='blue', nl=False)

    @staticmethod
    def _overwritten():
        click.secho('OVERWRITTEN ', fg='blue', nl=False)

    @staticmethod
    def _interrupted():
        click.secho('INTERRUPTED ', fg='blue', nl=False)

    @staticmethod
    def _dry_run():
        click.secho('DRY_RUN', fg='blue', nl=False)

    @staticmethod
    def _no_gitlab_project():
        click.secho('NO_GITLAB_PROJECT ', fg='red', nl=False)

    @staticmethod
    def _multiple_gitlab_projects():
        click.secho('MULTIPLE_GITLAB_PROJECTS ', fg='red', nl=False)
