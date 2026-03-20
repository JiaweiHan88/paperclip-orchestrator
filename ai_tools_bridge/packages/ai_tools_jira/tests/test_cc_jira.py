"""Tests for Jira connection and authentication functionality.

This module contains comprehensive tests for the CodeCraft JIRA instance creation,
authentication handling, and connection management.
"""

import unittest
from unittest.mock import Mock, patch

from ai_tools_jira.cc_jira import CodeCraftJira, get_cc_jira_instance


class TestCodeCraftJira(unittest.TestCase):
    """Test cases for the CodeCraftJira class.

    Tests JIRA instance initialization and configuration.
    """

    @patch("ai_tools_jira.instance.JIRA.__init__")
    def test_initialization_with_token_auth(self, mock_jira_init):
        """Test CodeCraftJira initialization with token authentication."""
        # Mock the parent JIRA __init__ to avoid actual connection
        mock_jira_init.return_value = None

        token = "test_token_123"

        # Initialize CodeCraftJira
        jira_instance = CodeCraftJira(token_auth=token)

        # Verify parent constructor was called with correct parameters
        expected_options = {
            "cookies": {"SMCHALLENGE": "YES"},
            "headers": {"Accept": "application/json", "Content-Type": "application/json"},
        }

        mock_jira_init.assert_called_once_with(
            server="https://jira.cc.bmwgroup.net",
            token_auth=token,
            options=expected_options,
        )

        # Verify host attribute is set
        self.assertEqual(jira_instance.host, "https://jira.cc.bmwgroup.net")

    @patch("ai_tools_jira.instance.JIRA.__init__")
    def test_initialization_with_different_tokens(self, mock_jira_init):
        """Test CodeCraftJira initialization with different token values."""
        # Mock the parent JIRA __init__
        mock_jira_init.return_value = None

        test_tokens = ["abc123", "xyz789", "token_with_special_chars!@#"]

        for token in test_tokens:
            with self.subTest(token=token):
                # Initialize CodeCraftJira
                jira_instance = CodeCraftJira(token_auth=token)

                # Verify token was passed correctly
                call_args = mock_jira_init.call_args
                self.assertEqual(call_args[1]["token_auth"], token)

    @patch("ai_tools_jira.instance.JIRA.__init__")
    def test_server_url_is_correct(self, mock_jira_init):
        """Test that the correct server URL is used."""
        # Mock the parent JIRA __init__
        mock_jira_init.return_value = None

        # Initialize CodeCraftJira
        jira_instance = CodeCraftJira(token_auth="test_token")

        # Verify server URL
        call_args = mock_jira_init.call_args
        self.assertEqual(call_args[1]["server"], "https://jira.cc.bmwgroup.net")
        self.assertEqual(jira_instance.host, "https://jira.cc.bmwgroup.net")

    @patch("ai_tools_jira.instance.JIRA.__init__")
    def test_options_configuration(self, mock_jira_init):
        """Test that options are configured correctly."""
        # Mock the parent JIRA __init__
        mock_jira_init.return_value = None

        # Initialize CodeCraftJira
        CodeCraftJira(token_auth="test_token")

        # Verify options configuration
        call_args = mock_jira_init.call_args
        options = call_args[1]["options"]

        # Check cookies
        self.assertIn("cookies", options)
        self.assertEqual(options["cookies"]["SMCHALLENGE"], "YES")

        # Check headers
        self.assertIn("headers", options)
        self.assertEqual(options["headers"]["Accept"], "application/json")
        self.assertEqual(options["headers"]["Content-Type"], "application/json")

    @patch("ai_tools_jira.instance.JIRA.__init__")
    def test_inheritance_from_jira(self, mock_jira_init):
        """Test that CodeCraftJira properly inherits from JIRA."""
        from jira import JIRA

        # Mock the parent JIRA __init__
        mock_jira_init.return_value = None

        # Initialize CodeCraftJira
        jira_instance = CodeCraftJira(token_auth="test_token")

        # Verify inheritance
        self.assertIsInstance(jira_instance, JIRA)


class TestGetCcJiraInstance(unittest.TestCase):
    """Test cases for the get_cc_jira_instance function.

    Tests the factory function for creating CodeCraftJira instances.
    """

    @patch("ai_tools_jira.cc_jira.CodeCraftJira")
    def test_returns_codecraft_jira_instance(self, mock_codecraft_jira_class):
        """Test that function returns a CodeCraftJira instance."""
        # Setup mock
        mock_instance = Mock()
        mock_codecraft_jira_class.return_value = mock_instance

        token = "factory_test_token"

        # Call function
        result = get_cc_jira_instance(token)

        # Verify CodeCraftJira was instantiated with correct token
        mock_codecraft_jira_class.assert_called_once_with(token_auth=token)

        # Verify the instance is returned
        self.assertEqual(result, mock_instance)

    @patch("ai_tools_jira.cc_jira.CodeCraftJira")
    def test_passes_token_correctly(self, mock_codecraft_jira_class):
        """Test that token is passed correctly to CodeCraftJira."""
        # Setup mock
        mock_instance = Mock()
        mock_codecraft_jira_class.return_value = mock_instance

        test_tokens = ["token1", "another_token_123", "complex_token!@#$%"]

        for token in test_tokens:
            with self.subTest(token=token):
                # Reset mock
                mock_codecraft_jira_class.reset_mock()

                # Call function
                get_cc_jira_instance(token)

                # Verify token was passed correctly
                mock_codecraft_jira_class.assert_called_once_with(token_auth=token)

    @patch("ai_tools_jira.cc_jira.CodeCraftJira")
    def test_returns_jira_interface(self, mock_codecraft_jira_class):
        """Test that returned object has JIRA interface."""
        from jira import JIRA

        # Setup mock to simulate JIRA interface
        mock_instance = Mock(spec=JIRA)
        mock_codecraft_jira_class.return_value = mock_instance

        # Call function
        result = get_cc_jira_instance("test_token")

        # Verify result has expected JIRA methods (using spec)
        # This ensures the mock has the same interface as JIRA
        self.assertTrue(hasattr(result, "issue"))  # Common JIRA method
        self.assertEqual(result, mock_instance)

    @patch("ai_tools_jira.cc_jira.CodeCraftJira")
    def test_factory_exception_propagation(self, mock_codecraft_jira_class):
        """Test that exceptions during CodeCraftJira creation are propagated."""
        # Setup mock to raise exception
        mock_codecraft_jira_class.side_effect = Exception("Connection failed")

        # Call function and expect exception
        with self.assertRaises(Exception) as context:
            get_cc_jira_instance("test_token")

        self.assertEqual(str(context.exception), "Connection failed")


if __name__ == "__main__":
    unittest.main()
