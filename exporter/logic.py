import requests
import git
import re

from exporter.helpers import ensure_tmp_dir


class GitHubClient:
    """
    This class can communicate with the GitHub API
    just give it a token and go.
    """
    API = 'https://api.github.com'

    def __init__(self, token, session=None):
        self.token = token
        self.session = session or requests.Session()
        self.session.headers = {'User-Agent': 'exporter'}
        self.session.auth = self._token_auth

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

    def user(self):
        return self._paginated_json_get(f'{self.API}/user')

    def commits(self, reposlug, params):
        return self.get(url=f'{self.API}/repos/{reposlug}/commits', params=params)

    def statuses(self, reposlug, ref):
        return self.get(url=f'{self.API}/repos/{reposlug}/commits/{ref}/statuses')

    def add_status(self, reposlug, ref, status):
        response = self.session.post(
            url=f'{self.API}/repos/{reposlug}/commits/{ref}/statuses',
            json=status
        )
        response.raise_for_status()
        return response.json()

    def get(self, url: str, params=None):
        return self._paginated_json_get(url=url, params=params)


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


class TaskStream:
    pass


class Exporter:

    def __init__(self, github, gitlab, logger):
        self.github = github
        self.gitlab = gitlab
        self.logger = logger

    def _fetch_gitlab_project(self, project_name, tmp):
        r = self.gitlab.search_owned_projects(project_name)
        if len(r) == 0:
            raise ValueError(f'Multiple projects found for {project_name}')
        if len(r[0]) == 0:
            raise ValueError(f'No project found for {project_name}')
        json = r[0]

        username = json['owner']['username']
        password = self.gitlab.token
        auth_https_url = re.sub(r'(https://)', f'\\1{username}:{password}@', json['http_url_to_repo'])

        return git.Git(tmp).clone(auth_https_url)

    def run(self, projects, tmp_dir=None):
        with ensure_tmp_dir(tmp_dir) as tmp:
            for project_name in projects:
                repo = self._fetch_gitlab_project(project_name, tmp)
