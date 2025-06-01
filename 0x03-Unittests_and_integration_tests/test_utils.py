#!/usr/bin/env python3   #Tells system to use python3
"""
The test for utils.py

This files contains unit test for functions for functions in the utils module.
"""
#Importing the required modules
import unittest
from parameterized import parameterized
from  typing import Any, Dict, Tuple
from unittest.mock import patch
from unittest.mock import Mock
from utils import access_nested_map, get_json, memoize

# TASK 0: PARAMETERIZE A UNIT TEST FOR ACCESS_NESTED_MAP



class TestAccessNestedMap(unittest.TestCase):
    """
    Test cases for the access_nested_map function.
    
    This class tests that access_nested_map correctly navigates through
    nested dictionaries using a path (tuple of keys).
    """
    
    @parameterized.expand([
        # Each tuple represents one test case: (input_dict, path_tuple, expected_result)
        ({"a": 1}, ("a",), 1),                           # Test 1: Simple key access
        ({"a": {"b": 2}}, ("a",), {"b": 2}),            # Test 2: Get nested dict
        ({"a": {"b": 2}}, ("a", "b"), 2),               # Test 3: Deep navigation
    ])
    def test_access_nested_map(
        self, 
        nested_map: Dict[str, Any],      # The dictionary to navigate
        path: Tuple[str, ...],           # The path (sequence of keys) to follow
        expected: Any                    # What we expect the function to return
    ) -> None:
        """
        Test that access_nested_map returns the expected result for valid inputs.
        
        Args:
            nested_map: Dictionary to navigate through
            path: Tuple of keys defining the path to follow
            expected: The value we expect to be returned
        """
        # This is the actual test - call the function and check the result
        result = access_nested_map(nested_map, path)
        self.assertEqual(result, expected)

    # TASK 1: Test that KeyError exceptions are raised.
    @parameterized.expand([
        # Each tuple set(inputa_dict,_invalid_path, expected_exception_type)
        ({},("a",), KeyError),
        ({"a":1},("a", "b"), KeyError),
    ])
    def test_access_nested_map_exception(
        self,
        nested_map:Dict[str, Any],
        path: Tuple[str, ...],
        expected_exception: type
    ) -> None:
        
        """
        Test that access_nested_map raises KeyError for invalid paths

        Args:
            nested_map: Dictionary to navigate through
            path: Invalid oath that should raise an exception
            expected_exception: The exception type we expect to be raiseed.
        """
        # Use assertRaises context manager to test exception cases
        with self.assertRaises(expected_exception):
            access_nested_map(nested_map, path)

# TASK 2: MOCT HTTP calls for get_json_function
class TestGetJson(unittest.TestCase):
    """
    Test cases for the get_json function.
    
    This class tests that get_json correctly makes HTTP requests and returns
    the JSON response. We mock requests.get to avoid real HTTP calls.
    """
    
    @parameterized.expand([
        # Each tuple: (test_url, expected_json_payload)
        ("http://example.com", {"payload": True}),
        ("http://holberton.io", {"payload": False}),
    ])
    @patch('utils.requests.get')  # This replaces requests.get with a mock
    def test_get_json(
        self, 
        test_url: str,                  # URL to test with
        test_payload: Dict[str, Any],   # Expected JSON response
        mock_get: Mock                  # The mock object (injected by @patch)
    ) -> None:
        """
        Test that get_json returns expected result and calls requests.get once.
        
        Args:
            test_url: The URL to pass to get_json
            test_payload: The JSON data we expect to be returned
            mock_get: Mock object that replaces requests.get
        """
        # Step 1: Set up the mock to return what we want
        mock_response = Mock()                          # Create a mock response object
        mock_response.json.return_value = test_payload  # When .json() called, return our test data
        mock_get.return_value = mock_response           # When requests.get called, return our mock response
        
        # Step 2: Call the function we're testing
        result = get_json(test_url)
        
        # Step 3: Verify the mock was called correctly
        mock_get.assert_called_once_with(test_url)      # Check requests.get was called once with correct URL
        
        # Step 4: Verify the result is what we expected
        self.assertEqual(result, test_payload)          # Check the function returned the right data

#TASK 3: Test memoize decorator with patch
class TestMemoize(unittest.TestCase):
    """
    Test cases for the memoize decorator.
    
    This class tests that the memoize decorator correctly caches method results
    so that the underlying method is only called once.
    """
    
    def test_memoize(self) -> None:
        """
        Test that memoize decorator caches method results properly.
        
        We create a test class with a memoized property, call it twice,
        and verify the underlying method is only called once.
        """
        
        # Step 1: Define a test class inside our test method
        class TestClass:
            """Test class to demonstrate memoization"""
            
            def a_method(self):
                """Method that returns 42 - we'll mock this"""
                return 42

            @memoize
            def a_property(self):
                """Memoized property that calls a_method"""
                return self.a_method()
        
        # Step 2: Create an instance of our test class
        test_instance = TestClass()
        
        # Step 3: Use patch.object to mock the a_method on our specific instance
        with patch.object(test_instance, 'a_method', return_value=42) as mock_method:
            # Step 4: Call the memoized property twice
            result1 = test_instance.a_property  # First call - should call a_method
            result2 = test_instance.a_property  # Second call - should use cache
            
            # Step 5: Verify both calls returned the correct result
            self.assertEqual(result1, 42)
            self.assertEqual(result2, 42)
            
            # Step 6: Verify a_method was only called once (proof of memoization)
            mock_method.assert_called_once()


# Running the tests upon file execution
if __name__ == '__main__':
    unittest.main()