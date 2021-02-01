import requests
import re
from threading import Thread
from abc import ABC
import enlighten

# API reference: https://gitpython.readthedocs.io/en/stable/reference.html
import git

from .helpers import ensure_tmp_dir


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

    def _post(self, url, data=None):
        r = self.session.post(url=url, json=data)
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

    def create_repo(self, repo_name, data=None):
        data = data or dict()
        data['name'] = repo_name
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

    def run(self):
        pass


class TaskFetchGitlabProject(TaskBase):

    def __init__(self, gitlab, project_name, base_dir, bar):
        self.gitlab = gitlab
        self.project_name = project_name
        self.base_dir = base_dir
        self.bar = bar

    def run(self):
        self.bar.unit = 'Searching for project'
        r = self.gitlab.search_owned_projects(self.project_name)
        self.bar.update()
        if len(r) == 0:
            raise ValueError(f'Multiple projects found for {self.project_name}')
        if len(r[0]) == 0:
            raise ValueError(f'No project found for {self.project_name}')
        json = r[0]

        username = json['owner']['username']
        password = self.gitlab.token
        url = json['http_url_to_repo']
        auth_https_url = re.sub(r'(https://)', f'\\1{username}:{password}@', url)
        self.bar.unit = 'Cloning GitLab repo'
        repo = git.Repo.clone_from(auth_https_url, self.base_dir / self.project_name)
        self.bar.update()
        self.bar.unit = 'Fetching GitLab LFS files'
        git.cmd.Git(working_dir=repo.working_dir).execute(['git', 'lfs', 'fetch', '--all'])  # fetching all references
        self.bar.update()
        self.bar.unit = ''
        return repo


class TaskPushToGitHub(TaskBase):

    def __init__(self, github, git_repo, repo_name, bar):
        self.github = github
        self.git_repo = git_repo
        self.repo_name = repo_name
        self.bar = bar

    def run(self):
        self.bar.unit = 'Creating GitHub repo'
        self.github.create_repo(self.repo_name)
        self.bar.update()
        owner = self.github.login
        password = self.github.token
        auth_https_url = f'https://{owner}:{password}@github.com/{owner}/{self.repo_name}.git'
        remote = self.git_repo.create_remote(f'github_{self.repo_name}', auth_https_url)
        self.bar.unit = 'Pushing to GitHub'
        remote.push()
        self.bar.update()
        self.bar.unit = ''


class TaskExportProject(TaskBase):

    def __init__(self, github, gitlab, project_name, base_dir, prefix, bar):
        self.github = github
        self.gitlab = gitlab
        self.project_name = project_name
        self.base_dir = base_dir
        self.prefix = prefix
        self.bar = bar

    def run(self):
        fetch = TaskFetchGitlabProject(self.gitlab, self.project_name, self.base_dir, self.bar)
        repo = fetch.run()

        push = TaskPushToGitHub(self.github, repo, self.prefix + self.project_name, self.bar)
        push.run()


class TaskProgressBarPool(TaskBase):
    """
    API documentation: https://python-enlighten.readthedocs.io/en/stable/api.html
    """

    def __init__(self):
        self.pool = []
        self.manager = enlighten.get_manager()
        self.bar_format = '{desc}{desc_pad}{percentage:3.0f}%|{bar}| {count:{len_total}d}/{total:d} [{unit}]'

    def register(self, name, total):
        bar = self.manager.counter(total=total, desc=name, unit="ticks", color="red", bar_format=self.bar_format,
                                   autorefresh=False)
        self.pool.append(bar)
        return bar

    def run(self):
        while any([x.total != x.total for x in self.pool]):
            for bar in self.pool:
                bar.refresh()


class Exporter:

    def __init__(self, github, gitlab, logger):
        self.github = github
        self.gitlab = gitlab
        self.logger = logger

    def run(self, projects, force_overwrite=False, tmp_dir=None, prefix='github_'):
        with ensure_tmp_dir(tmp_dir) as tmp:
            bar = TaskProgressBarPool()
            tasks = list(
                map(lambda name: TaskExportProject(self.github, self.gitlab, name, tmp, prefix, bar.register(name, 5)),
                    projects))
            tasks.append(bar)
            self.exucute_tasks(tasks)

    def exucute_tasks(self, tasks):
        threads = []
        for task in tasks:
            t = Thread(target=task.run)
            t.start()
            threads.append(t)
        for t in threads:
            t.join()
