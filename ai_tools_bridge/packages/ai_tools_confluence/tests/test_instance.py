"""Tests for Confluence instance creation and configuration.

This module tests the creation and configuration of CodeCraft and ATC Confluence instances,
ensuring proper initialization and authentication setup.
"""

import unittest
from unittest.mock import patch, ANY

from ai_tools_confluence.instance import (
    ATCConfluence,
    CodeCraftConfluence,
    get_atc_confluence,
    get_cc_confluence,
)


class TestCodeCraftConfluence(unittest.TestCase):
    """Test cases for CodeCraftConfluence class.

    Tests initialization and configuration of the CodeCraft Confluence instance.
    """

    @patch("ai_tools_confluence.instance.Confluence.__init__")
    def test_initialization_with_valid_token(self, mock_super_init):
        """Test that CodeCraftConfluence initializes correctly with valid token."""
        mock_super_init.return_value = None
        token = "test_token_123"

        confluence = CodeCraftConfluence(token=token)

        # Verify that the parent Confluence class was initialized with correct parameters
        mock_super_init.assert_called_once_with(
            url="https://confluence.cc.bmwgroup.net",
            token=token,
            cloud=False,
            session=ANY,
        )
        self.assertIsInstance(confluence, CodeCraftConfluence)

    @patch("ai_tools_confluence.instance.Confluence.__init__")
    def test_initialization_with_empty_token(self, mock_super_init):
        """Test that CodeCraftConfluence can be initialized with empty token."""
        mock_super_init.return_value = None
        token = ""

        confluence = CodeCraftConfluence(token=token)

        mock_super_init.assert_called_once_with(
            url="https://confluence.cc.bmwgroup.net",
            token=token,
            cloud=False,
            session=ANY,
        )
        self.assertIsInstance(confluence, CodeCraftConfluence)

    @patch("ai_tools_confluence.instance.Confluence.__init__")
    def test_uses_correct_url(self, mock_super_init):
        """Test that CodeCraftConfluence uses the correct BMW CC URL."""
        mock_super_init.return_value = None

        CodeCraftConfluence(token="test_token")

        call_args = mock_super_init.call_args
        self.assertEqual(call_args.kwargs["url"], "https://confluence.cc.bmwgroup.net")

    @patch("ai_tools_confluence.instance.Confluence.__init__")
    def test_uses_server_mode_not_cloud(self, mock_super_init):
        """Test that CodeCraftConfluence is configured for server mode, not cloud."""
        mock_super_init.return_value = None

        CodeCraftConfluence(token="test_token")

        call_args = mock_super_init.call_args
        self.assertFalse(call_args.kwargs["cloud"])


class TestATCConfluence(unittest.TestCase):
    """Test cases for ATCConfluence class.

    Tests initialization and configuration of the ATC Confluence instance.
    """

    @patch("ai_tools_confluence.instance.Confluence.__init__")
    def test_initialization_with_valid_token(self, mock_super_init):
        """Test that ATCConfluence initializes correctly with valid token."""
        mock_super_init.return_value = None
        token = "test_atc_token_456"

        confluence = ATCConfluence(token=token)

        mock_super_init.assert_called_once_with(
            url="https://atc.bmwgroup.net/confluence",
            token=token,
            cloud=False,
            session=ANY,
        )
        self.assertIsInstance(confluence, ATCConfluence)

    @patch("ai_tools_confluence.instance.Confluence.__init__")
    def test_uses_correct_url(self, mock_super_init):
        """Test that ATCConfluence uses the correct ATC URL."""
        mock_super_init.return_value = None

        ATCConfluence(token="test_token")

        call_args = mock_super_init.call_args
        self.assertEqual(call_args.kwargs["url"], "https://atc.bmwgroup.net/confluence")

    @patch("ai_tools_confluence.instance.Confluence.__init__")
    def test_uses_server_mode_not_cloud(self, mock_super_init):
        """Test that ATCConfluence is configured for server mode, not cloud."""
        mock_super_init.return_value = None

        ATCConfluence(token="test_token")

        call_args = mock_super_init.call_args
        self.assertFalse(call_args.kwargs["cloud"])


class TestGetCCConfluence(unittest.TestCase):
    """Test cases for get_cc_confluence function.

    Tests the factory function for creating CodeCraft Confluence instances.
    """

    @patch("ai_tools_confluence.instance.Confluence.__init__")
    def test_returns_codecraft_instance(self, mock_super_init):
        """Test that get_cc_confluence returns a CodeCraftConfluence instance."""
        mock_super_init.return_value = None
        token = "factory_test_token"

        result = get_cc_confluence(token=token)

        self.assertIsInstance(result, CodeCraftConfluence)

    @patch("ai_tools_confluence.instance.Confluence.__init__")
    def test_passes_token_correctly(self, mock_super_init):
        """Test that get_cc_confluence passes the token to the constructor."""
        mock_super_init.return_value = None
        token = "specific_token_123"

        get_cc_confluence(token=token)

        mock_super_init.assert_called_once()
        call_args = mock_super_init.call_args
        self.assertEqual(call_args.kwargs["token"], token)


class TestGetATCConfluence(unittest.TestCase):
    """Test cases for get_atc_confluence function.

    Tests the factory function for creating ATC Confluence instances.
    """

    @patch("ai_tools_confluence.instance.Confluence.__init__")
    def test_returns_atc_instance(self, mock_super_init):
        """Test that get_atc_confluence returns an ATCConfluence instance."""
        mock_super_init.return_value = None
        token = "atc_factory_test_token"

        result = get_atc_confluence(token=token)

        self.assertIsInstance(result, ATCConfluence)

    @patch("ai_tools_confluence.instance.Confluence.__init__")
    def test_passes_token_correctly(self, mock_super_init):
        """Test that get_atc_confluence passes the token to the constructor."""
        mock_super_init.return_value = None
        token = "atc_specific_token_456"

        get_atc_confluence(token=token)

        mock_super_init.assert_called_once()
        call_args = mock_super_init.call_args
        self.assertEqual(call_args.kwargs["token"], token)


if __name__ == "__main__":
    unittest.main()
