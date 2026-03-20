"""Tests for BaseBmwJira base class functionality.

This module contains comprehensive tests for the BaseBmwJira class which provides
common JIRA connection configuration for BMW JIRA instances.
"""

import unittest
from unittest.mock import patch

from ai_tools_jira.instance import BaseBmwJira


class TestBaseBmwJiraInitialization(unittest.TestCase):
    """Test cases for BaseBmwJira initialization.

    Tests the base JIRA class configuration including host setup,
    token handling, and JIRA options.
    """

    @patch("ai_tools_jira.instance.JIRA.__init__")
    def test_initialization_with_explicit_token(self, mock_jira_init):
        """Test BaseBmwJira initialization with an explicit token provided."""
        mock_jira_init.return_value = None

        host = "jira.example.com"
        token = "test_token_123"

        instance = BaseBmwJira(host=host, token=token)

        expected_options = {
            "cookies": {"SMCHALLENGE": "YES"},
            "headers": {"Accept": "application/json", "Content-Type": "application/json"},
        }

        mock_jira_init.assert_called_once_with(
            server="https://jira.example.com",
            token_auth=token,
            options=expected_options,
        )

        self.assertEqual(instance.host, "https://jira.example.com")

    @patch("ai_tools_jira.instance.get_token")
    @patch("ai_tools_jira.instance.JIRA.__init__")
    def test_initialization_without_token_uses_get_token(self, mock_jira_init, mock_get_token):
        """Test BaseBmwJira retrieves token from get_token when none provided."""
        mock_jira_init.return_value = None
        mock_get_token.return_value = "retrieved_token"

        host = "jira.example.com"

        instance = BaseBmwJira(host=host)

        mock_get_token.assert_called_once_with(host)
        mock_jira_init.assert_called_once()
        call_args = mock_jira_init.call_args
        self.assertEqual(call_args[1]["token_auth"], "retrieved_token")

    @patch("ai_tools_jira.instance.get_token")
    @patch("ai_tools_jira.instance.JIRA.__init__")
    def test_initialization_with_none_token_uses_get_token(self, mock_jira_init, mock_get_token):
        """Test BaseBmwJira retrieves token when token is explicitly None."""
        mock_jira_init.return_value = None
        mock_get_token.return_value = "auto_retrieved_token"

        host = "jira.example.com"

        BaseBmwJira(host=host, token=None)

        mock_get_token.assert_called_once_with(host)
        call_args = mock_jira_init.call_args
        self.assertEqual(call_args[1]["token_auth"], "auto_retrieved_token")

    @patch("ai_tools_jira.instance.JIRA.__init__")
    def test_host_url_construction(self, mock_jira_init):
        """Test that host URL is constructed correctly with https prefix."""
        mock_jira_init.return_value = None

        test_hosts = [
            ("example.com", "https://example.com"),
            ("jira.cc.bmwgroup.net", "https://jira.cc.bmwgroup.net"),
            ("atc.bmwgroup.net/jira", "https://atc.bmwgroup.net/jira"),
        ]

        for host_input, expected_url in test_hosts:
            with self.subTest(host=host_input):
                instance = BaseBmwJira(host=host_input, token="test_token")
                self.assertEqual(instance.host, expected_url)

    @patch("ai_tools_jira.instance.JIRA.__init__")
    def test_options_contain_correct_cookies(self, mock_jira_init):
        """Test that options contain the SMCHALLENGE cookie for SSO bypass."""
        mock_jira_init.return_value = None

        BaseBmwJira(host="jira.example.com", token="test_token")

        call_args = mock_jira_init.call_args
        options = call_args[1]["options"]

        self.assertIn("cookies", options)
        self.assertEqual(options["cookies"]["SMCHALLENGE"], "YES")

    @patch("ai_tools_jira.instance.JIRA.__init__")
    def test_options_contain_correct_headers(self, mock_jira_init):
        """Test that options contain the correct JSON content headers."""
        mock_jira_init.return_value = None

        BaseBmwJira(host="jira.example.com", token="test_token")

        call_args = mock_jira_init.call_args
        options = call_args[1]["options"]

        self.assertIn("headers", options)
        self.assertEqual(options["headers"]["Accept"], "application/json")
        self.assertEqual(options["headers"]["Content-Type"], "application/json")

    @patch("ai_tools_jira.instance.JIRA.__init__")
    def test_inheritance_from_jira(self, mock_jira_init):
        """Test that BaseBmwJira properly inherits from JIRA."""
        from jira import JIRA

        mock_jira_init.return_value = None

        instance = BaseBmwJira(host="jira.example.com", token="test_token")

        self.assertIsInstance(instance, JIRA)


class TestBaseBmwJiraTokenHandling(unittest.TestCase):
    """Test cases for BaseBmwJira token handling edge cases.

    Tests various token scenarios including empty strings and special characters.
    """

    @patch("ai_tools_jira.instance.get_token")
    @patch("ai_tools_jira.instance.JIRA.__init__")
    def test_empty_string_token_uses_get_token(self, mock_jira_init, mock_get_token):
        """Test that empty string token triggers get_token lookup."""
        mock_jira_init.return_value = None
        mock_get_token.return_value = "fallback_token"

        BaseBmwJira(host="jira.example.com", token="")

        mock_get_token.assert_called_once_with("jira.example.com")

    @patch("ai_tools_jira.instance.JIRA.__init__")
    def test_token_with_special_characters(self, mock_jira_init):
        """Test that tokens with special characters are passed correctly."""
        mock_jira_init.return_value = None

        special_token = "token_with!@#$%^&*()_special_chars"

        BaseBmwJira(host="jira.example.com", token=special_token)

        call_args = mock_jira_init.call_args
        self.assertEqual(call_args[1]["token_auth"], special_token)


if __name__ == "__main__":
    unittest.main()
