"""Tests for ATCJira connection and authentication functionality.

This module contains comprehensive tests for the ATC JIRA instance creation,
authentication handling, and connection management.
"""

import unittest
from unittest.mock import patch

from ai_tools_jira.atc_jira import ATCJira


class TestATCJira(unittest.TestCase):
    """Test cases for the ATCJira class.

    Tests ATC JIRA instance initialization and configuration.
    """

    @patch("ai_tools_jira.instance.JIRA.__init__")
    def test_initialization_with_token_auth(self, mock_jira_init):
        """Test ATCJira initialization with token authentication."""
        mock_jira_init.return_value = None

        token = "test_token_123"

        jira_instance = ATCJira(token_auth=token)

        expected_options = {
            "cookies": {"SMCHALLENGE": "YES"},
            "headers": {"Accept": "application/json", "Content-Type": "application/json"},
        }

        mock_jira_init.assert_called_once_with(
            server="https://atc.bmwgroup.net/jira",
            token_auth=token,
            options=expected_options,
        )

        self.assertEqual(jira_instance.host, "https://atc.bmwgroup.net/jira")

    @patch("ai_tools_jira.instance.JIRA.__init__")
    def test_initialization_with_different_tokens(self, mock_jira_init):
        """Test ATCJira initialization with different token values."""
        mock_jira_init.return_value = None

        test_tokens = ["abc123", "xyz789", "token_with_special_chars!@#"]

        for token in test_tokens:
            with self.subTest(token=token):
                jira_instance = ATCJira(token_auth=token)

                call_args = mock_jira_init.call_args
                self.assertEqual(call_args[1]["token_auth"], token)

    @patch("ai_tools_jira.instance.JIRA.__init__")
    def test_server_url_is_correct(self, mock_jira_init):
        """Test that the correct ATC server URL is used."""
        mock_jira_init.return_value = None

        jira_instance = ATCJira(token_auth="test_token")

        call_args = mock_jira_init.call_args
        self.assertEqual(call_args[1]["server"], "https://atc.bmwgroup.net/jira")
        self.assertEqual(jira_instance.host, "https://atc.bmwgroup.net/jira")

    @patch("ai_tools_jira.instance.JIRA.__init__")
    def test_options_configuration(self, mock_jira_init):
        """Test that options are configured correctly."""
        mock_jira_init.return_value = None

        ATCJira(token_auth="test_token")

        call_args = mock_jira_init.call_args
        options = call_args[1]["options"]

        self.assertIn("cookies", options)
        self.assertEqual(options["cookies"]["SMCHALLENGE"], "YES")

        self.assertIn("headers", options)
        self.assertEqual(options["headers"]["Accept"], "application/json")
        self.assertEqual(options["headers"]["Content-Type"], "application/json")

    @patch("ai_tools_jira.instance.JIRA.__init__")
    def test_inheritance_from_jira(self, mock_jira_init):
        """Test that ATCJira properly inherits from JIRA."""
        from jira import JIRA

        mock_jira_init.return_value = None

        jira_instance = ATCJira(token_auth="test_token")

        self.assertIsInstance(jira_instance, JIRA)

    @patch("ai_tools_jira.instance.JIRA.__init__")
    def test_inheritance_from_base_bmw_jira(self, mock_jira_init):
        """Test that ATCJira properly inherits from BaseBmwJira."""
        from ai_tools_jira.instance import BaseBmwJira

        mock_jira_init.return_value = None

        jira_instance = ATCJira(token_auth="test_token")

        self.assertIsInstance(jira_instance, BaseBmwJira)


if __name__ == "__main__":
    unittest.main()
