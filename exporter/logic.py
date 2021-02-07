import click
import requests
import re
import shutil
import uuid
import git  # API reference: https://gitpython.readthedocs.io/en/stable/reference.html
import enlighten

from threading import Thread
from abc import ABC
from .helpers import ensure_tmp_dir, rndstr


class GitHubClient:
    """
    This class can communicate with the GitHub API
    just give it a token and go.

    API documentation: https://docs.github.com/en/free-pro-team@latest/rest/reference
    """
    API = 'https://api.github.com'

    def __init__(self, token, session=None):
        self.token = token
        self.session = session or requests.Session()
        self.session.headers = {'User-Agent': 'exporter'}
        self.session.auth = self._token_auth
        self._login = None

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
    This class can communicate with the GitLab API
    just give it a token and go.

    API documentation: https://gitlab.fit.cvut.cz/help/api/README.md
    """
    API = 'https://gitlab.fit.cvut.cz/api/v4'

    def __init__(self, token, session=None):
        self.token = token
        self.session = session or requests.Session()
        self.session.headers = {'User-Agent': 'exporter'}
        self.session.auth = self._token_auth

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

    def __init__(self):
        self.id = str(uuid.uuid4())  # make a random UUID
        self.running = False
        self.exc = []  # list of caught exceptions during execution
        self.subtasks = []  # list of subtasks used by this task
        self.suppress_exceptions = False  # if false suppress any exception throwing

    def run(self):
        pass

    def stop(self):
        self.running = False
        for task in self.subtasks:
            task.stop()

    def raise_if_not_running(self):
        if not self.running:
            raise InterruptedError(self.id)

    def rollback(self):
        for task in self.subtasks:
            task.rollback()


class TaskFetchGitlabProject(TaskBase):

    def __init__(self, gitlab, name_gitlab, base_dir, bar, suppress_exceptions):
        super().__init__()
        self.gitlab = gitlab
        self.name_gitlab = name_gitlab
        self.base_dir = base_dir
        self.bar = bar
        self.suppress_exceptions = suppress_exceptions
        self.id = name_gitlab

    def run(self):
        try:
            self.running = True
            self.bar.set_msg('Searching for project')
            r = self.gitlab.search_owned_projects(self.name_gitlab)
            self.bar.set_msg_and_update('Searching for project done')
            if len(r) == 0:
                raise ValueError(f'Multiple projects found for {self.name_gitlab}')
            if len(r[0]) == 0:
                raise ValueError(f'No project found for {self.name_gitlab}')
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
            if not self.suppress_exceptions:
                raise


class TaskPushToGitHub(TaskBase):

    def __init__(self, github, git_cmd, name_github, is_private, bar, suppress_exceptions):
        super().__init__()
        self.github = github
        self.git_cmd = git_cmd
        self.name_github = name_github
        self.is_private = is_private
        self.bar = bar
        self.id = git_cmd
        self.suppress_exceptions = suppress_exceptions

    def run(self):
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
            remote.push()
            self.bar.set_msg_and_update('Pushing to GitHub done')
            self.running = False
        except Exception as e:
            self.running = False
            self.exc.append(e)
            if not self.suppress_exceptions:
                raise


class TaskExportProject(TaskBase):

    def __init__(self, gitlab, github, name_gitlab, name_github, is_github_private,
                 base_dir, bar, conflict_policy, suppress_exceptions):
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

    def run(self):
        try:
            self.running = True
            self.github_repo_existed = self.github.repo_exists(self.name_github, self.github.login)
            if self.github_repo_existed:
                if self.conflict_policy in ['skip', 'porcelain']:
                    print(
                        f"Skipping export for GitLab project '{self.name_gitlab}'. "
                        f"Project name '{self.name_github}' already exists on GitHub.")
                    self.bar.set_msg_and_finish('SKIPPED')
                    self.running = False
                    return
                elif self.conflict_policy in ['overwrite']:
                    self.bar.set_msg('Deleting GitHubProject')
                    print(f'Overwriting GitHub project {self.name_github}')
                    self.github.delete_repo(self.name_github, self.github.login)
                    self.bar.set_msg('GitHub project deleted')

            task_fetch_gitlab_project = TaskFetchGitlabProject(
                gitlab=self.gitlab,
                name_gitlab=self.name_gitlab,
                base_dir=self.base_dir,
                bar=self.bar,
                suppress_exceptions=False
            )
            self.subtasks.append(task_fetch_gitlab_project)
            self.raise_if_not_running()
            self.bar.set_msg('Starting fetching GitLab project')
            git_cmd = task_fetch_gitlab_project.run()
            self.bar.set_msg('Fetching GitLab project done')

            task_push_to_github = TaskPushToGitHub(
                github=self.github,
                git_cmd=git_cmd,
                name_github=self.name_github,
                is_private=self.is_github_private,
                bar=self.bar,
                suppress_exceptions=False
            )
            self.subtasks.append(task_push_to_github)
            self.raise_if_not_running()
            self.bar.set_msg('Starting pushing to GitHub')
            task_push_to_github.run()
            self.bar.set_msg_and_finish('DONE')
            self.running = False
        except Exception as e:
            self.running = False
            self.exc.append(e)
            self.bar.set_msg('RUN ERROR')
            if not self.suppress_exceptions:
                raise

    def rollback(self):
        try:
            for task in self.subtasks:
                task.rollback()
            if not self.github_repo_existed:
                self.github.delete_repo(self.name_github, self.github.login)
            self.bar.set_msg('ROLLBACKED')
        except Exception as e:
            if not self.suppress_exceptions:
                raise
            self.exc.append(e)
            self.bar.set_msg('ROLLBACK ERROR')


class ProgressBarWrapper:

    def __init__(self, bar):
        self.bar = bar
        self.set_msg('')

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
    API documentation: https://python-enlighten.readthedocs.io/en/stable/api.html
    """

    def __init__(self):
        super().__init__()
        self.pool = []
        self.manager = enlighten.get_manager()
        self.bar_format = '{desc}{desc_pad}{percentage:3.0f}%|{bar}| {count:{len_total}d}/{total:d} [{unit}]'
        self.id = 'Progress Bar'

    def register(self, name, total):
        bar = self.manager.counter(total=total, desc=name, unit="ticks", color="red", bar_format=self.bar_format,
                                   autorefresh=False, threaded=True)
        bar_wrapper = ProgressBarWrapper(bar)
        self.pool.append(bar_wrapper)
        return bar_wrapper

    def run(self):
        self.running = True
        while not all([x.is_finished() for x in self.pool]) and self.running:
            for bar in self.pool:
                bar.refresh()
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

    def run(self, projects, conflict_policy, tmp_dir, task_timeout):
        tasks = []
        threads = []
        tmp_dir = ensure_tmp_dir(tmp_dir)
        try:
            tasks = self._prepare_tasks(
                gitlab=self.gitlab,
                github=self.github,
                projects=projects,
                tmp_dir=tmp_dir,
                conflict_policy=conflict_policy,
                debug=self.debug,
                suppress_exceptions=not self.debug
            )
            self._execute_tasks(
                tasks=tasks,
                threads=threads
            )
        except KeyboardInterrupt:
            self._handle_keyboard_interrupt(tasks, threads, task_timeout)
        except Exception as e:
            self._handle_generic_exception(tasks, threads, task_timeout, e)
        finally:
            shutil.rmtree(tmp_dir)

    @staticmethod
    def _prepare_tasks(gitlab, github, projects, tmp_dir, conflict_policy, debug, suppress_exceptions):
        tasks = []
        bar_task = TaskProgressBarPool()
        for name_gitlab, name_github, visibility_github in projects:
            if name_gitlab == name_github:
                bar_msg = f'[{name_gitlab}]'
            else:
                bar_msg = f'[{name_gitlab} -> {name_github}]'
            bar = bar_task.register(bar_msg, 5)
            tasks.append(TaskExportProject(
                gitlab=gitlab,
                github=github,
                name_gitlab=name_gitlab,
                name_github=name_github,
                is_github_private=visibility_github == 'private',
                base_dir=tmp_dir,
                bar=bar,
                conflict_policy=conflict_policy,
                suppress_exceptions=suppress_exceptions
            ))
        tasks.append(bar_task)
        return tasks

    @staticmethod
    def _execute_tasks(tasks, threads):
        for task in tasks:
            t = Thread(target=task.run, args=())
            t.start()
            threads.append(t)
        for t in threads:
            t.join()

    @staticmethod
    def _rollback(tasks):
        for task in tasks:
            click.echo(f"ROLLBACK: '{task.id}'")
            task.rollback()

    @staticmethod
    def _stop_execution(tasks, threads, task_timeout):
        for task in tasks:
            task.stop()
        for t in threads:
            t.join(task_timeout)

    def _handle_keyboard_interrupt(self, tasks, threads, task_timeout):
        click.secho(f'STOPPING', bold=True)
        self._stop_execution(tasks, threads, task_timeout)
        self._rollback(tasks)

    def _handle_generic_exception(self, tasks, threads, task_timeout, exception):
        click.secho(f'ERROR: {exception}', fg='red', bold=True)
        self._stop_execution(tasks, threads, task_timeout)
        self._rollback(tasks)
