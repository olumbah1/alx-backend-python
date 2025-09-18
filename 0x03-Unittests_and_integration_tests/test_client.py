#!/usr/bin/env python3
"""
Unit tests for the GithubOrgClient class.
"""

import unittest
from unittest.mock import patch, PropertyMock
from parameterized import parameterized
from client import GithubOrgClient


class TestGithubOrgClient(unittest.TestCase):
    """
    Test cases for GithubOrgClient.org property.
    """

    @parameterized.expand([
        ("google",),
        ("abc",),
    ])
    @patch("client.get_json")
    def test_org(self, org_name, mock_get_json):
        """
        Test that GithubOrgClient.org returns the correct value
        and get_json is called with the correct URL.
        """
        expected_url = f"https://api.github.com/orgs/{org_name}"
        mock_get_json.return_value = {"org": org_name}

        client = GithubOrgClient(org_name)
        result = client.org

        mock_get_json.assert_called_once_with(expected_url)
        self.assertEqual(result, {"org": org_name})


class TestGithubOrgClient(unittest.TestCase):
    """
    Test cases for GithubOrgClient class.
    """

    @patch.object(GithubOrgClient, "org", new_callable=PropertyMock)
    def test_public_repos_url(self, mock_org):
        """
        Test that _public_repos_url returns the correct repos_url
        from the mocked org payload.
        """
        payload = {"repos_url": "https://api.github.com/orgs/testorg/repos"}
        mock_org.return_value = payload

        client = GithubOrgClient("testorg")
        result = client._public_repos_url

        self.assertEqual(result, payload["repos_url"])

