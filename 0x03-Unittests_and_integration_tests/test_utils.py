#!/usr/bin/env python3
import unittest
from parameterized import parameterized
from utils import access_nested_map
from unittest.mock import patch, Mock
from utils import get_json
# class TestAccessNestedMap(unittest.TestCase):
#     @parameterized.expand([
#         ({"a": 1}, ("a",), 1),
#         ({"a": {"b": 2}}, ("a",), {"b": 2}),
#         ({"a": {"b": 2}}, ("a", "b"), 2),
#     ])
#     def test_access_nested_map(self, nested_map, path, expected):
#         self.assertEqual(access_nested_map(nested_map, path), expected)
        



# class TestAccessNestedMap(unittest.TestCase):
#     @parameterized.expand([
#         ({}, ("a",), 'a'),
#         ({"a": 1}, ("a", "b"), 'b'),
#     ])
#     def test_access_nested_map_exception(self, nested_map, path, missing_key):
#         with self.assertRaises(KeyError) as context:
#             access_nested_map(nested_map, path)
#         # Check that the exception message contains the missing key in quotes
#         self.assertEqual(str(context.exception), f"'{missing_key}'")



class TestGetJson(unittest.TestCase):
    @parameterized.expand([
        ("http://example.com", {"payload": True}),
        ("http://holberton.io", {"payload": False}),
    ])
    @patch("utils.requests.get")
    def test_get_json(self, test_url, test_payload, mock_get):
        # Configure the mock to return a response with .json() method returning test_payload
        mock_response = Mock()
        mock_response.json.return_value = test_payload
        mock_get.return_value = mock_response

        # Call the function
        result = get_json(test_url)

        # Check that requests.get was called once with test_url
        mock_get.assert_called_once_with(test_url)

        # Check that the result equals the test_payload
        self.assertEqual(result, test_payload)
