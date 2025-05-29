#!/usr/bin/env python3
"""Unit and integration tests for client module"""

import unittest
from parameterized import parameterized, parameterized_class
from unittest.mock import patch, PropertyMock, Mock
from client import GithubOrgClient
from fixtures import org_payload, repos_payload, expected_repos, apache2_repos


class TestGithubOrgClient(unittest.TestCase):
    """Unit tests for GithubOrgClient"""

    @parameterized.expand([
        ("google",),
        ("abc",)
    ])
    @patch('client.get_json')
    def test_org(self, org_name, mock_get_json):
        """Test GithubOrgClient.org returns correct value"""
        test_client = GithubOrgClient(org_name)
        test_client.org()
        mock_get_json.assert_called_once_with(f"https://api.github.com/orgs/{org_name}")

    def test_public_repos_url(self):
        """Test GithubOrgClient._public_repos_url returns correct value"""
        with patch('client.GithubOrgClient.org', new_callable=PropertyMock) as mock_org:
            mock_org.return_value = {"repos_url": "https://api.github.com/orgs/test/repos"}
            test_client = GithubOrgClient("test")
            result = test_client._public_repos_url
            self.assertEqual(result, "https://api.github.com/orgs/test/repos")

    @patch('client.get_json')
    def test_public_repos(self, mock_get_json):
        """Test GithubOrgClient.public_repos returns correct repos list"""
        test_payload = [{"name": "repo1"}, {"name": "repo2"}]
        mock_get_json.return_value = test_payload
        
        with patch('client.GithubOrgClient._public_repos_url', new_callable=PropertyMock) as mock_url:
            mock_url.return_value = "https://api.github.com/orgs/test/repos"
            test_client = GithubOrgClient("test")
            
            result = test_client.public_repos()
            
            self.assertEqual(result, ["repo1", "repo2"])
            mock_url.assert_called_once()
            mock_get_json.assert_called_once_with("https://api.github.com/orgs/test/repos")

    @parameterized.expand([
        ({"license": {"key": "my_license"}}, "my_license", True),
        ({"license": {"key": "other_license"}}, "my_license", False)
    ])
    def test_has_license(self, repo, license_key, expected):
        """Test GithubOrgClient.has_license returns correct boolean"""
        test_client = GithubOrgClient("test")
        result = test_client.has_license(repo, license_key)
        self.assertEqual(result, expected)


@parameterized_class([
    {
        "org_payload": org_payload,
        "repos_payload": repos_payload,
        "expected_repos": expected_repos,
        "apache2_repos": apache2_repos
    }
])
class TestIntegrationGithubOrgClient(unittest.TestCase):
    """Integration tests for GithubOrgClient"""

    @classmethod
    def setUpClass(cls):
        """Set up class by mocking requests.get"""
        cls.get_patcher = patch('requests.get')
        cls.mock_get = cls.get_patcher.start()
        
        def side_effect(url):
            mock = Mock()
            if url.endswith("/orgs/test"):
                mock.json.return_value = cls.org_payload
            elif url.endswith("/repos"):
                mock.json.return_value = cls.repos_payload
            return mock
            
        cls.mock_get.side_effect = side_effect

    @classmethod
    def tearDownClass(cls):
        """Tear down class by stopping patcher"""
        cls.get_patcher.stop()

    def test_public_repos(self):
        """Test public_repos in integration setting"""
        test_client = GithubOrgClient("test")
        result = test_client.public_repos()
        self.assertEqual(result, self.expected_repos)

    def test_public_repos_with_license(self):
        """Test public_repos with license filter in integration setting"""
        test_client = GithubOrgClient("test")
        result = test_client.public_repos(license="apache-2.0")
        self.assertEqual(result, self.apache2_repos)


if __name__ == '__main__':
    unittest.main()
    