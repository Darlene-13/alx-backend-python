#!/usr/bin/env python3
"""Test client module for GithubOrgClient"""

import unittest
from unittest.mock import patch, PropertyMock
from parameterized import parameterized, parameterized_class
from client import GithubOrgClient
from fixtures import TEST_PAYLOAD


class TestGithubOrgClient(unittest.TestCase):
    """Test class for GithubOrgClient"""

    @parameterized.expand([
        ("google",),
        ("abc",),
    ])
    @patch('client.get_json')
    def test_org(self, org_name, mock_get_json):
        """Test that GithubOrgClient.org returns the correct value"""
        test_payload = {"name": org_name}
        mock_get_json.return_value = test_payload
        
        client = GithubOrgClient(org_name)
        result = client.org
        
        expected_url = f"https://api.github.com/orgs/{org_name}"
        mock_get_json.assert_called_once_with(expected_url)
        self.assertEqual(result, test_payload)

    def test_public_repos_url(self):
        """Unit test for GithubOrgClient._public_repos_url"""
        with patch('client.GithubOrgClient.org', new_callable=PropertyMock) as mock_org:
            test_payload = {"repos_url": "https://api.github.com/orgs/google/repos"}
            mock_org.return_value = test_payload
            
            client = GithubOrgClient("google")
            result = client._public_repos_url
            
            self.assertEqual(result, test_payload["repos_url"])

    @patch('client.get_json')
    def test_public_repos(self, mock_get_json):
        """Unit test for GithubOrgClient.public_repos"""
        test_payload = [
            {"name": "repo1"},
            {"name": "repo2"},
            {"name": "repo3"}
        ]
        mock_get_json.return_value = test_payload
        
        with patch('client.GithubOrgClient._public_repos_url', new_callable=PropertyMock) as mock_repos_url:
            test_url = "https://api.github.com/orgs/google/repos"
            mock_repos_url.return_value = test_url
            
            client = GithubOrgClient("google")
            result = client.public_repos()
            
            expected = ["repo1", "repo2", "repo3"]
            self.assertEqual(result, expected)
            
            mock_repos_url.assert_called_once()
            mock_get_json.assert_called_once_with(test_url)

    @parameterized.expand([
        ({"license": {"key": "my_license"}}, "my_license", True),
        ({"license": {"key": "other_license"}}, "my_license", False),
    ])
    def test_has_license(self, repo, license_key, expected):
        """Unit test for GithubOrgClient.has_license"""
        client = GithubOrgClient("google")
        result = client.has_license(repo, license_key)
        self.assertEqual(result, expected)


@parameterized_class([
    {
        "org_payload": TEST_PAYLOAD[0][0],
        "repos_payload": TEST_PAYLOAD[0][1],
        "expected_repos": TEST_PAYLOAD[0][2],
        "apache2_repos": TEST_PAYLOAD[0][3],
    }
])
class TestIntegrationGithubOrgClient(unittest.TestCase):
    """Integration test class for GithubOrgClient"""
    
    @classmethod
    def setUpClass(cls):
        """Set up class method to start patching requests.get"""
        def side_effect(url):
            """Side effect function for mocking requests.get"""
            class MockResponse:
                def __init__(self, json_data):
                    self.json_data = json_data
                
                def json(self):
                    return self.json_data
            
            if url == "https://api.github.com/orgs/google":
                return MockResponse(cls.org_payload)
            elif url == "https://api.github.com/orgs/google/repos":
                return MockResponse(cls.repos_payload)
            return MockResponse(None)
        
        cls.get_patcher = patch('requests.get', side_effect=side_effect)
        cls.get_patcher.start()

    @classmethod
    def tearDownClass(cls):
        """Tear down class method to stop patching"""
        cls.get_patcher.stop()

    def test_public_repos(self):
        """Integration test for public_repos method"""
        client = GithubOrgClient("google")
        result = client.public_repos()
        self.assertEqual(result, self.expected_repos)

    def test_public_repos_with_license(self):
        """Integration test for public_repos with license filter"""
        client = GithubOrgClient("google")
        result = client.public_repos(license="apache-2.0")
        self.assertEqual(result, self.apache2_repos)


if __name__ == '__main__':
    unittest.main()