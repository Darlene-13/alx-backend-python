# Import the class we want to test from client module
from client import GithubOrgClient

# We'll also need PropertyMock for Task 5 and parameterized_class for Task 8
from unittest.mock import patch, Mock, PropertyMock
from parameterized import parameterized, parameterized_class

# Import fixtures for Task 8
from fixtures import TEST_PAYLOAD#!/usr/bin/env python3
"""
Test module for client.py

This file contains tests for the GithubOrgClient class.
We'll build it step by step, starting with Task 4.
"""

# Step 1: Import all the modules we need
import unittest                          # For creating test cases
from unittest.mock import patch, Mock    # For mocking dependencies
from parameterized import parameterized  # For running same test with different data
from typing import Any, Dict, List      # For type hints (good practice)

# Import the class we want to test from client module
from client import GithubOrgClient

# We'll also need PropertyMock for Task 5
from unittest.mock import patch, Mock, PropertyMock


# ============================================================================
# TASK 4: Parameterize and patch as decorators
# ============================================================================

class TestGithubOrgClient(unittest.TestCase):
    """
    Test cases for the GithubOrgClient class.
    
    This class tests various methods of GithubOrgClient while mocking
    external dependencies like HTTP calls.
    """
    
    @parameterized.expand([
        # Each tuple represents one test case: (org_name,)
        ("google",),    # Test with Google organization
        ("abc",),       # Test with ABC organization  
    ])
    @patch('client.get_json')  # This replaces client.get_json with a mock
    def test_org(
        self, 
        org_name: str,        # The organization name to test with
        mock_get_json: Mock   # The mock object (injected by @patch)
    ) -> None:
        """
        Test that GithubOrgClient.org returns the correct value.
        
        This test verifies that:
        1. The org property calls get_json with the correct URL
        2. The org property returns the data from get_json
        
        Args:
            org_name: Name of the organization to test
            mock_get_json: Mock object that replaces get_json function
        """
        # Step 1: Set up the expected URL and mock response
        expected_url = f"https://api.github.com/orgs/{org_name}"
        expected_payload = {
            "login": org_name,
            "id": 12345,
            "repos_url": f"https://api.github.com/orgs/{org_name}/repos"
        }
        
        # Step 2: Configure the mock to return our test data
        mock_get_json.return_value = expected_payload
        
        # Step 3: Create a GithubOrgClient instance and call the org property
        client = GithubOrgClient(org_name)
        result = client.org  # This should trigger the @memoize decorated method
        
        # Step 4: Verify the mock was called correctly
        # Check that get_json was called exactly once with the expected URL
        mock_get_json.assert_called_once_with(expected_url)
        
        # Step 5: Verify the result is what we expected
        self.assertEqual(result, expected_payload)

    # ========================================================================
    # TASK 5: Mocking a property
    # ========================================================================
    
    def test_public_repos_url(self) -> None:
        """
        Test that _public_repos_url returns the expected URL from org data.
        
        This test verifies that the _public_repos_url property correctly
        extracts the repos_url from the org property data.
        
        The challenge here is that _public_repos_url depends on the org 
        property, so we need to mock the org property to return known data.
        """
        # Step 1: Define the payload that the org property should return
        # This simulates what the GitHub API would return for an organization
        org_payload = {
            "login": "google",
            "id": 1342004,
            "repos_url": "https://api.github.com/orgs/google/repos",
            "description": "Google ❤️ Open Source"
        }
        
        # Step 2: Use patch.object as context manager to mock the org property
        # We use PropertyMock because org is a property (accessed with dot notation)
        with patch.object(
            GithubOrgClient,          # The class to patch
            'org',                    # The property name to patch  
            new_callable=PropertyMock,# Use PropertyMock for properties
            return_value=org_payload  # What the property should return
        ) as mock_org:
            
            # Step 3: Create a client instance (org_name doesn't matter since we're mocking)
            client = GithubOrgClient("test_org")
            
            # Step 4: Call the _public_repos_url property
            result = client._public_repos_url
            
            # Step 5: Verify the result is the repos_url from our mocked payload
            expected_url = org_payload["repos_url"]
            self.assertEqual(result, expected_url)
            
            # Step 6: Verify that the org property was accessed
            # (This is optional but good practice to verify our mock was used)
            mock_org.assert_called_once()

    # ========================================================================
    # TASK 6: More patching - Multiple mocks in one test
    # ========================================================================
    
    @patch('client.get_json')  # Mock the get_json function
    def test_public_repos(self, mock_get_json: Mock) -> None:
        """
        Test that public_repos returns expected list of repository names.
        
        This test is more complex because public_repos() method:
        1. Uses _public_repos_url property (which uses org property)
        2. Calls get_json with that URL
        3. Extracts repo names from the response
        
        We need to mock both get_json and _public_repos_url.
        """
        # Step 1: Define the payload that get_json should return
        # This simulates what GitHub API returns for /orgs/{org}/repos
        repos_payload = [
            {
                "name": "repo1",
                "full_name": "google/repo1", 
                "license": {"key": "mit"},
                "private": False
            },
            {
                "name": "repo2",
                "full_name": "google/repo2",
                "license": {"key": "apache-2.0"},
                "private": False
            },
            {
                "name": "repo3", 
                "full_name": "google/repo3",
                "license": None,  # Some repos have no license
                "private": False
            }
        ]
        
        # Step 2: Configure the get_json mock to return our test data
        mock_get_json.return_value = repos_payload
        
        # Step 3: Mock the _public_repos_url property using context manager
        # We need this because public_repos() calls get_json(self._public_repos_url)
        test_repos_url = "https://api.github.com/orgs/google/repos"
        
        with patch.object(
            GithubOrgClient,
            '_public_repos_url', 
            new_callable=PropertyMock,
            return_value=test_repos_url
        ) as mock_repos_url:
            
            # Step 4: Create client and call the public_repos method
            client = GithubOrgClient("google")
            result = client.public_repos()
            
            # Step 5: Verify the result contains expected repository names
            expected_repo_names = ["repo1", "repo2", "repo3"]
            self.assertEqual(result, expected_repo_names)
            
            # Step 6: Verify that _public_repos_url property was accessed once
            mock_repos_url.assert_called_once()
            
            # Step 7: Verify that get_json was called once with the correct URL
            mock_get_json.assert_called_once_with(test_repos_url)

    # ========================================================================
    # TASK 7: Parameterize - Testing pure logic (no mocking needed)
    # ========================================================================
    
    @parameterized.expand([
        # Each tuple: (repo_data, license_key_to_check, expected_result)
        ({"license": {"key": "my_license"}}, "my_license", True),
        ({"license": {"key": "other_license"}}, "my_license", False),
    ])
    def test_has_license(
        self, 
        repo: Dict[str, Any],    # Repository data dict
        license_key: str,        # License key to check for
        expected: bool           # Expected boolean result
    ) -> None:
        """
        Test that has_license returns expected boolean value.
        
        This is a pure logic test - no mocking needed because has_license
        doesn't make any external calls or depend on other methods.
        It just examines the data structure passed to it.
        
        Args:
            repo: Dictionary representing repository data
            license_key: The license key to look for
            expected: Whether we expect the license to match
        """
        # Step 1: Create a client instance (org name doesn't matter for this test)
        client = GithubOrgClient("test_org")
        
        # Step 2: Call the has_license method with our test data
        result = client.has_license(repo, license_key)
        
        # Step 3: Verify the result matches our expectation
        self.assertEqual(result, expected)


# ============================================================================
# TASK 8: Integration test with fixtures
# ============================================================================

@parameterized_class([
    {
        "org_payload": TEST_PAYLOAD[0][0],      # Organization data from fixtures
        "repos_payload": TEST_PAYLOAD[0][1],    # Repository list data from fixtures  
        "expected_repos": TEST_PAYLOAD[0][2],   # Expected repo names from fixtures
        "apache2_repos": TEST_PAYLOAD[0][3],    # Expected Apache 2.0 repos from fixtures
    }
])
class TestIntegrationGithubOrgClient(unittest.TestCase):
    """
    Integration tests for GithubOrgClient.
    
    Integration tests are different from unit tests:
    - Unit tests: Mock everything, test one method in isolation
    - Integration tests: Mock only external dependencies, test workflows end-to-end
    
    Here we only mock requests.get (the external HTTP calls) but let all the
    GithubOrgClient methods work together naturally.
    """
    
    @classmethod
    def setUpClass(cls) -> None:
        """
        Set up class-level fixtures that run once before all test methods.
        
        This method:
        1. Creates a mock for requests.get
        2. Configures it to return different responses based on URL
        3. Starts the patcher so it's active for all tests in this class
        """
        def side_effect_function(url: str):
            """
            Mock side effect function that returns appropriate responses
            based on the URL being requested.
            
            Args:
                url: The URL that requests.get was called with
                
            Returns:
                Mock response object with json() method
            """
            # Create a mock response object
            mock_response = Mock()
            
            # Determine what to return based on the URL
            if url == f"https://api.github.com/orgs/{cls.org_payload['login']}":
                # If requesting org info, return org_payload
                mock_response.json.return_value = cls.org_payload
            elif url == cls.org_payload["repos_url"]:
                # If requesting repos list, return repos_payload  
                mock_response.json.return_value = cls.repos_payload
            else:
                # For any other URL, return empty dict
                mock_response.json.return_value = {}
                
            return mock_response
        
        # Start the patcher for requests.get
        # We patch 'requests.get' because get_json imports and uses requests directly
        cls.get_patcher = patch('requests.get', side_effect=side_effect_function)
        cls.get_patcher.start()
    
    @classmethod  
    def tearDownClass(cls) -> None:
        """
        Clean up class-level fixtures that run once after all test methods.
        
        This stops the patcher to restore the original requests.get function.
        """
        cls.get_patcher.stop()
    
    def test_public_repos(self) -> None:
        """
        Integration test for public_repos method without license filter.
        
        This test verifies the complete workflow:
        1. GithubOrgClient.__init__() sets org_name
        2. public_repos() calls _public_repos_url property
        3. _public_repos_url calls org property  
        4. org calls get_json() with org URL
        5. get_json() calls requests.get() [MOCKED]
        6. public_repos() calls get_json() with repos URL  
        7. get_json() calls requests.get() again [MOCKED]
        8. public_repos() processes the response and returns repo names
        """
        # Create client with the org name from our fixtures
        client = GithubOrgClient(self.org_payload["login"])
        
        # Call public_repos() - this triggers the entire workflow
        result = client.public_repos()
        
        # Verify we get the expected list of repository names
        self.assertEqual(result, self.expected_repos)
    
    def test_public_repos_with_license(self) -> None:
        """
        Integration test for public_repos method with license filter.
        
        This test verifies the same workflow as above, but with license filtering:
        - Call public_repos("apache-2.0") 
        - Should return only repos with Apache 2.0 license
        """
        # Create client with the org name from our fixtures  
        client = GithubOrgClient(self.org_payload["login"])
        
        # Call public_repos() with license filter
        result = client.public_repos("apache-2.0")
        
        # Verify we get only the Apache 2.0 licensed repositories
        self.assertEqual(result, self.apache2_repos)


# ============================================================================
# Run the tests if this file is executed directly  
# ============================================================================
if __name__ == '__main__':
    unittest.main()