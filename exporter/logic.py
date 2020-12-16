import requests

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
    """
    API = 'https://gitlab.fit.cvut.cz/api/v4/'

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


class TaskStream:
    pass


class Exporter:

    def __init__(self, github, gitlab, logger):
        self.github = github
        self.gitlab = gitlab
        self.logger = logger

    def run(self, task_stream, tmp_dir=None):
        with ensure_tmp_dir(tmp_dir) as tmp:
            pass
