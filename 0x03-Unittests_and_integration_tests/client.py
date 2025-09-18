#!/usr/bin/env python3
"""
A github org client
"""
import requests
from functools import wraps


def memoize(fn):
    """
    Decorator to memoize method
    """
    attr_name = '_cache_' + fn.__name__

    @wraps(fn)
    def memoized(self):
        """"memoized wraps"""
        if not hasattr(self, attr_name):
            setattr(self, attr_name, fn(self))
        return getattr(self, attr_name)
    return memoized


def get_json(url):
    """
    Method that returns the JSON response of a URL
    """
    req = requests.get(url)
    return req.json()


class GithubOrgClient:
    """
    A Gitub org client
    """
    ORG_URL = "https://api.github.com/orgs/{org}"

    def __init__(self, org_name):
        """
        Init method of GithubOrgClient
        """
        self._org_name = org_name

    @memoize
    def org(self):
        """
        Memoize org
        """
        return get_json(self.ORG_URL.format(org=self._org_name))

    @property
    def _public_repos_url(self):
        """
        Property to get repos_url from org
        """
        return self.org["repos_url"]

    def public_repos(self, license=None):
        """
        Public repos
        """
        json_payload = get_json(self._public_repos_url)
        public_repos = [
            repo["name"] for repo in json_payload
            if license is None or self.has_license(repo, license)
        ]

        return public_repos

    @staticmethod
    def has_license(repo, license_key):
        """
        Static method to check if repo has license
        """
        assert license_key is not None, "license_key cannot be None"
        if repo["license"] is None:
            return False
        return repo["license"]["key"] == license_key