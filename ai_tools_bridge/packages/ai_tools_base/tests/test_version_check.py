"""Tests for version_check module."""

import warnings
from unittest.mock import MagicMock, patch

import pytest

from ai_tools_base.version_check import (
    check_version_compatibility,
    get_ai_tools_packages,
    get_own_version,
    get_version_info,
    try_parse_base_version,
)


class TestTryParseBaseVersion:
    """Tests for try_parse_base_version function."""

    def test_simple_version(self):
        assert try_parse_base_version("1.2.3") == (1, 2, 3)

    def test_version_with_dev(self):
        assert try_parse_base_version("1.2.3.dev1") == (1, 2, 3)

    def test_version_with_post(self):
        assert try_parse_base_version("1.2.3.post1") == (1, 2, 3)

    def test_version_with_local(self):
        assert try_parse_base_version("1.2.3+local") == (1, 2, 3)

    def test_complex_version(self):
        assert try_parse_base_version("1.2.3.post1.dev0+git.abc123.dirty") == (1, 2, 3)

    def test_two_part_version_raises_error(self):
        with pytest.raises(ValueError, match="Version string does not have three parts"):
            try_parse_base_version("1.2")

    def test_one_part_version_raises_error(self):
        with pytest.raises(ValueError, match="Version string does not have three parts"):
            try_parse_base_version("1")

    def test_invalid_version_raises_error(self):
        with pytest.raises(ValueError, match="Version string does not have three parts"):
            try_parse_base_version("invalid")

    def test_dirty_version_raises_error(self):
        with pytest.raises(ValueError, match="Version string does not have three parts"):
            try_parse_base_version("dirty")


class TestWarningMessage:
    """Tests for warning message content."""

    def test_warning_with_parseable_version(self):
        with patch(
            "ai_tools_base.version_check.get_ai_tools_packages",
            return_value={
                "ai-tools-base": "1.0.0",
                "ai-tools-mcp": "1.1.0",
            },
        ):
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                result = check_version_compatibility()

        assert result is False
        assert len(w) == 1
        assert issubclass(w[0].category, UserWarning)
        warning_msg = str(w[0].message)
        assert "uv sync --reinstall" in warning_msg
        assert "pip install" in warning_msg
        assert "ai-tools-base" in warning_msg
        assert ">=1.1.0" in warning_msg

    def test_warning_includes_fix_commands(self):
        with patch(
            "ai_tools_base.version_check.get_ai_tools_packages",
            return_value={
                "ai-tools-base": "1.0.0",
                "ai-tools-mcp": "1.1.0",
            },
        ):
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                check_version_compatibility()

        warning_msg = str(w[0].message)
        assert "To fix, run one of:" in warning_msg
        assert "uv sync --reinstall" in warning_msg
        assert "pip install --upgrade" in warning_msg

    def test_warning_for_unparseable_versions(self):
        """Unparseable versions should still warn but with simpler fix message."""
        with patch(
            "ai_tools_base.version_check.get_ai_tools_packages",
            return_value={
                "ai-tools-base": "dirty+git.abc123",
                "ai-tools-mcp": "dirty+git.def456",
            },
        ):
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                result = check_version_compatibility()

        assert result is False
        assert len(w) == 1
        warning_msg = str(w[0].message)
        assert "uv sync --reinstall" in warning_msg


class TestGetAIToolsPackages:
    """Tests for get_ai_tools_packages function."""

    def test_finds_ai_tools_packages(self):
        mock_dist1 = MagicMock()
        mock_dist1.metadata = {"Name": "ai-tools-base", "Version": "1.0.0"}

        mock_dist2 = MagicMock()
        mock_dist2.metadata = {"Name": "ai_tools_mcp", "Version": "1.0.0"}

        mock_dist3 = MagicMock()
        mock_dist3.metadata = {"Name": "other-package", "Version": "2.0.0"}

        with patch("ai_tools_base.version_check.distributions", return_value=[mock_dist1, mock_dist2, mock_dist3]):
            packages = get_ai_tools_packages()

        assert "ai-tools-base" in packages
        assert "ai-tools-mcp" in packages
        assert "other-package" not in packages

    def test_duplicate_packages_raises_error(self):
        mock_dist1 = MagicMock()
        mock_dist1.metadata = {"Name": "ai-tools-base", "Version": "1.0.0"}

        mock_dist2 = MagicMock()
        mock_dist2.metadata = {"Name": "ai_tools_base", "Version": "1.0.1"}

        with patch("ai_tools_base.version_check.distributions", return_value=[mock_dist1, mock_dist2]):
            with pytest.raises(ValueError, match="Duplicate package detected"):
                get_ai_tools_packages()


class TestCheckVersionCompatibility:
    """Tests for check_version_compatibility function."""

    def test_compatible_identical_versions(self):
        with patch(
            "ai_tools_base.version_check.get_ai_tools_packages",
            return_value={
                "ai-tools-base": "1.0.0",
                "ai-tools-mcp": "1.0.0",
            },
        ):
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                result = check_version_compatibility()

        assert result is True
        assert len(w) == 0

    def test_incompatible_different_versions_warns(self):
        """Different version strings are incompatible, even if base is same."""
        with patch(
            "ai_tools_base.version_check.get_ai_tools_packages",
            return_value={
                "ai-tools-base": "1.0.0",
                "ai-tools-mcp": "1.0.0.dev1",
            },
        ):
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                result = check_version_compatibility()

        assert result is False
        assert len(w) == 1

    def test_incompatible_dirty_versions_warns(self):
        """Different dirty versions are incompatible."""
        with patch(
            "ai_tools_base.version_check.get_ai_tools_packages",
            return_value={
                "ai-tools-base": "1.0.0+git.abc123.dirty",
                "ai-tools-mcp": "1.0.0+git.def456.dirty",
            },
        ):
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                result = check_version_compatibility()

        assert result is False
        assert len(w) == 1

    def test_compatible_identical_dirty_versions(self):
        """Identical dirty versions are compatible."""
        with patch(
            "ai_tools_base.version_check.get_ai_tools_packages",
            return_value={
                "ai-tools-base": "1.0.0+git.abc123.dirty",
                "ai-tools-mcp": "1.0.0+git.abc123.dirty",
            },
        ):
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                result = check_version_compatibility()

        assert result is True
        assert len(w) == 0

    def test_incompatible_versions_warns(self):
        with patch(
            "ai_tools_base.version_check.get_ai_tools_packages",
            return_value={
                "ai-tools-base": "1.0.0",
                "ai-tools-mcp": "1.1.0",
            },
        ):
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                result = check_version_compatibility()

        assert result is False
        assert len(w) == 1

    def test_single_package(self):
        with patch(
            "ai_tools_base.version_check.get_ai_tools_packages",
            return_value={
                "ai-tools-base": "1.0.0",
            },
        ):
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                result = check_version_compatibility()

        assert result is True
        assert len(w) == 0

    def test_no_packages(self):
        with patch("ai_tools_base.version_check.get_ai_tools_packages", return_value={}):
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                result = check_version_compatibility()

        assert result is True
        assert len(w) == 0


class TestGetOwnVersion:
    """Tests for get_own_version function."""

    def test_returns_version_string(self):
        version = get_own_version()
        assert isinstance(version, str)
        assert len(version) > 0


class TestGetVersionInfo:
    """Tests for get_version_info function."""

    def test_returns_dict(self):
        with patch(
            "ai_tools_base.version_check.get_ai_tools_packages",
            return_value={
                "ai-tools-base": "1.0.0",
                "ai-tools-mcp": "1.0.1",
            },
        ):
            info = get_version_info()

        assert info == {"ai-tools-base": "1.0.0", "ai-tools-mcp": "1.0.1"}
