"""Tests for authentication utilities in ai_tools_base.auth module."""

import os
from unittest import mock

import pytest

from ai_tools_base.auth import get_token


class TestGetToken:
    """Test cases for the get_token function.

    Requirements tested:
    - Token retrieval from environment variables
    - Token retrieval from .netrc files
    - Fallback behavior from env vars to .netrc
    - Error handling when no token is found
    - Support for string and list inputs
    - Common names functionality
    - Proper error messages with attempted locations
    """

    def test_get_token_from_env_var_string(self):
        """Test retrieving token from environment variable using string input."""
        with mock.patch.dict(os.environ, {"TEST_TOKEN": "env_token_value"}):
            token = get_token(env_names="TEST_TOKEN")
            assert token == "env_token_value"

    def test_get_token_from_env_var_list(self):
        """Test retrieving token from environment variable using list input."""
        with mock.patch.dict(os.environ, {"TEST_TOKEN_2": "env_token_value_2"}):
            token = get_token(env_names=["TEST_TOKEN_1", "TEST_TOKEN_2"])
            assert token == "env_token_value_2"

    def test_get_token_from_env_var_first_match(self):
        """Test that first matching environment variable is used."""
        env_vars = {"TEST_TOKEN_1": "first_token", "TEST_TOKEN_2": "second_token"}
        with mock.patch.dict(os.environ, env_vars):
            token = get_token(env_names=["TEST_TOKEN_1", "TEST_TOKEN_2"])
            assert token == "first_token"

    def test_get_token_from_netrc_string(self):
        """Test retrieving token from .netrc file using string input."""
        # Mock netrc data
        mock_netrc_instance = mock.Mock()
        mock_netrc_instance.hosts = {"example.com": ("user", "account", "netrc_token")}

        with mock.patch("ai_tools_base.auth.netrc", return_value=mock_netrc_instance):
            with mock.patch.dict(os.environ, {}, clear=True):  # Clear env vars
                token = get_token(netrc_names="example.com")
                assert token == "netrc_token"

    def test_get_token_from_netrc_list(self):
        """Test retrieving token from .netrc file using list input."""
        mock_netrc_instance = mock.Mock()
        mock_netrc_instance.hosts = {
            "example.com": ("user", "account", "netrc_token"),
            "other.com": ("user", "account", "other_token"),
        }

        with mock.patch("ai_tools_base.auth.netrc", return_value=mock_netrc_instance):
            with mock.patch.dict(os.environ, {}, clear=True):
                token = get_token(netrc_names=["missing.com", "example.com"])
                assert token == "netrc_token"

    def test_get_token_env_var_priority_over_netrc(self):
        """Test that environment variables have priority over .netrc."""
        mock_netrc_instance = mock.Mock()
        mock_netrc_instance.hosts = {"example.com": ("user", "account", "netrc_token")}

        with mock.patch("ai_tools_base.auth.netrc", return_value=mock_netrc_instance):
            with mock.patch.dict(os.environ, {"TEST_TOKEN": "env_token"}):
                token = get_token(env_names="TEST_TOKEN", netrc_names="example.com")
                assert token == "env_token"

    def test_get_token_fallback_to_netrc(self):
        """Test fallback from environment variables to .netrc."""
        mock_netrc_instance = mock.Mock()
        mock_netrc_instance.hosts = {"example.com": ("user", "account", "netrc_token")}

        with mock.patch("ai_tools_base.auth.netrc", return_value=mock_netrc_instance):
            with mock.patch.dict(os.environ, {}, clear=True):
                token = get_token(env_names="MISSING_TOKEN", netrc_names="example.com")
                assert token == "netrc_token"

    def test_get_token_common_names_string(self):
        """Test using common_names parameter with string input."""
        with mock.patch.dict(os.environ, {"COMMON_TOKEN": "common_value"}):
            token = get_token(common_names="COMMON_TOKEN")
            assert token == "common_value"

    def test_get_token_common_names_list(self):
        """Test using common_names parameter with list input."""
        with mock.patch.dict(os.environ, {"COMMON_TOKEN_2": "common_value_2"}):
            token = get_token(common_names=["COMMON_TOKEN_1", "COMMON_TOKEN_2"])
            assert token == "common_value_2"

    def test_get_token_common_names_with_netrc_fallback(self):
        """Test common_names fallback to .netrc when env var not found."""
        mock_netrc_instance = mock.Mock()
        mock_netrc_instance.hosts = {"common.example.com": ("user", "account", "common_netrc_token")}

        with mock.patch("ai_tools_base.auth.netrc", return_value=mock_netrc_instance):
            with mock.patch.dict(os.environ, {}, clear=True):
                token = get_token(common_names="common.example.com")
                assert token == "common_netrc_token"

    def test_get_token_common_names_with_specific_combined(self):
        """Test that specific env_names and netrc_names are combined with common_names."""
        mock_netrc_instance = mock.Mock()
        mock_netrc_instance.hosts = {"specific.com": ("user", "account", "specific_token")}

        with mock.patch("ai_tools_base.auth.netrc", return_value=mock_netrc_instance):
            with mock.patch.dict(os.environ, {}, clear=True):
                token = get_token(common_names="common_name", netrc_names="specific.com")
                assert token == "specific_token"

    def test_get_token_combined_lists_env_priority(self):
        """Test that env vars from both env_names and common_names are checked, with env_names first."""
        with mock.patch.dict(os.environ, {"SPECIFIC_TOKEN": "specific_env_value", "COMMON_TOKEN": "common_env_value"}):
            token = get_token(common_names="COMMON_TOKEN", env_names="SPECIFIC_TOKEN")
            assert token == "specific_env_value"

    def test_get_token_combined_lists_fallback_to_common(self):
        """Test fallback to common_names when specific env_names not found."""
        with mock.patch.dict(os.environ, {"COMMON_TOKEN": "common_env_value"}):
            token = get_token(common_names="COMMON_TOKEN", env_names="MISSING_TOKEN")
            assert token == "common_env_value"

    def test_get_token_combined_netrc_lists(self):
        """Test that netrc hosts from both netrc_names and common_names are checked."""
        mock_netrc_instance = mock.Mock()
        mock_netrc_instance.hosts = {"common.example.com": ("user", "account", "common_netrc_token")}

        with mock.patch("ai_tools_base.auth.netrc", return_value=mock_netrc_instance):
            with mock.patch.dict(os.environ, {}, clear=True):
                token = get_token(common_names="common.example.com", netrc_names="missing.com")
                assert token == "common_netrc_token"

    def test_get_token_empty_env_var_skipped(self):
        """Test that empty environment variables are skipped."""
        mock_netrc_instance = mock.Mock()
        mock_netrc_instance.hosts = {"example.com": ("user", "account", "netrc_token")}

        with mock.patch("ai_tools_base.auth.netrc", return_value=mock_netrc_instance):
            with mock.patch.dict(os.environ, {"EMPTY_TOKEN": ""}):
                token = get_token(env_names="EMPTY_TOKEN", netrc_names="example.com")
                assert token == "netrc_token"

    def test_get_token_empty_netrc_token_skipped(self):
        """Test that empty .netrc tokens are skipped."""
        mock_netrc_instance = mock.Mock()
        mock_netrc_instance.hosts = {
            "empty.com": ("user", "account", ""),
            "valid.com": ("user", "account", "valid_token"),
        }

        with mock.patch("ai_tools_base.auth.netrc", return_value=mock_netrc_instance):
            with mock.patch.dict(os.environ, {}, clear=True):
                token = get_token(netrc_names=["empty.com", "valid.com"])
                assert token == "valid_token"

    def test_get_token_netrc_file_not_found_handled(self):
        """Test that missing .netrc file is handled gracefully."""
        with mock.patch("ai_tools_base.auth.netrc", side_effect=FileNotFoundError("~/.netrc not found")):
            with mock.patch.dict(os.environ, {}, clear=True):
                with pytest.raises(ValueError, match="No token found"):
                    get_token(netrc_names="example.com")

    def test_get_token_netrc_permission_error_raised(self):
        """Test that permission errors when reading .netrc are properly raised."""
        with mock.patch("ai_tools_base.auth.netrc", side_effect=PermissionError("Permission denied: ~/.netrc")):
            with mock.patch.dict(os.environ, {}, clear=True):
                with pytest.raises(PermissionError, match="Cannot read .netrc file due to permission error"):
                    get_token(netrc_names="example.com")

    def test_get_token_netrc_parse_error_raised(self):
        """Test that parsing errors in .netrc file are properly raised."""
        from netrc import NetrcParseError

        with mock.patch(
            "ai_tools_base.auth.netrc",
            side_effect=NetrcParseError("bad follower token", "~/.netrc", 5),
        ):
            with mock.patch.dict(os.environ, {}, clear=True):
                with pytest.raises(NetrcParseError, match="Error reading .netrc file"):
                    get_token(netrc_names="example.com")

    def test_get_token_netrc_corrupted_file_error_raised(self):
        """Test that corrupted .netrc file errors are properly raised with context."""
        from netrc import NetrcParseError

        with mock.patch(
            "ai_tools_base.auth.netrc",
            side_effect=NetrcParseError("syntax error", "~/.netrc", 10),
        ):
            with mock.patch.dict(os.environ, {}, clear=True):
                with pytest.raises(NetrcParseError, match="Error reading .netrc file"):
                    get_token(netrc_names="example.com")

    def test_get_token_netrc_io_error_raised(self):
        """Test that I/O errors when reading .netrc are properly raised."""
        with mock.patch("ai_tools_base.auth.netrc", side_effect=OSError("Disk read error")):
            with mock.patch.dict(os.environ, {}, clear=True):
                with pytest.raises(OSError, match="Error reading .netrc file"):
                    get_token(netrc_names="example.com")

    def test_get_token_env_var_found_despite_netrc_issues(self):
        """Test that env var is used and netrc issues don't affect result."""
        # Even if netrc would fail, env var should be found first
        with mock.patch.dict(os.environ, {"TEST_TOKEN": "env_value"}):
            token = get_token(env_names="TEST_TOKEN", netrc_names="example.com")
            assert token == "env_value"

    def test_get_token_no_token_found_error_env_only(self):
        """Test error message when no token found with env vars only."""
        with mock.patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="No token found in environment variables: \\['MISSING_TOKEN'\\]"):
                get_token(env_names="MISSING_TOKEN")

    def test_get_token_no_token_found_error_netrc_only(self):
        """Test error message when no token found with netrc only."""
        mock_netrc_instance = mock.Mock()
        mock_netrc_instance.hosts = {}

        with mock.patch("ai_tools_base.auth.netrc", return_value=mock_netrc_instance):
            with mock.patch.dict(os.environ, {}, clear=True):
                with pytest.raises(ValueError, match="No token found in \\.netrc hosts: \\['missing\\.com'\\]"):
                    get_token(netrc_names="missing.com")

    def test_get_token_no_token_found_error_both(self):
        """Test error message when no token found with both env vars and netrc."""
        mock_netrc_instance = mock.Mock()
        mock_netrc_instance.hosts = {}

        with mock.patch("ai_tools_base.auth.netrc", return_value=mock_netrc_instance):
            with mock.patch.dict(os.environ, {}, clear=True):
                with pytest.raises(ValueError, match="No token found in environment variables.*or \\.netrc hosts"):
                    get_token(env_names="MISSING_TOKEN", netrc_names="missing.com")

    def test_get_token_no_parameters_error(self):
        """Test error when no parameters provided."""
        with mock.patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="No token found"):
                get_token()

    def test_get_token_none_parameters(self):
        """Test behavior when all parameters are None."""
        with mock.patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="No token found"):
                get_token(common_names=None, env_names=None, netrc_names=None)

    def test_get_token_real_scenario_zuul(self):
        """Test realistic scenario similar to the original ZUUL_TOKEN code."""
        mock_netrc_instance = mock.Mock()
        mock_netrc_instance.hosts = {"zuul.cc.bmwgroup.net": ("user", "account", "zuul_netrc_token")}

        with mock.patch("ai_tools_base.auth.netrc", return_value=mock_netrc_instance):
            with mock.patch.dict(os.environ, {}, clear=True):
                token = get_token(env_names="ZUUL_TOKEN", netrc_names="zuul.cc.bmwgroup.net")
                assert token == "zuul_netrc_token"

    def test_get_token_real_scenario_github(self):
        """Test realistic scenario for GitHub token retrieval."""
        with mock.patch.dict(os.environ, {"GITHUB_TOKEN": "github_env_token"}):
            token = get_token(
                env_names=["GITHUB_TOKEN", "GH_TOKEN"], netrc_names=["github.com", "cc-github.bmwgroup.net"]
            )
            assert token == "github_env_token"
