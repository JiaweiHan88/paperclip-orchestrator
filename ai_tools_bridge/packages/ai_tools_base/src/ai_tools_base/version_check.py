"""Version compatibility checking for ai-tools-* packages.

This module provides automatic version compatibility checking for all installed
packages that start with 'ai-tools-' or 'ai_tools_'. When imported, it verifies
that all such packages have the same version string.

If a version mismatch is detected, it emits a warning with instructions on how
to update all packages to the highest available version.
"""

import re
import warnings
from importlib.metadata import distributions, version


def get_ai_tools_packages() -> dict[str, str]:
    """Get all installed packages that match ai-tools-* or ai_tools_* pattern.

    Returns:
        Dictionary mapping package names to version strings.
    """
    pattern = re.compile(r"^ai[-_]tools[-_]", re.IGNORECASE)
    packages: dict[str, str] = {}

    for dist in distributions():
        name = dist.metadata.get("Name")

        if not name:
            raise ValueError("Distribution without a Name metadata field found.")

        if not pattern.match(name):
            continue

        normalized = name.lower().replace("_", "-")

        if normalized in packages:
            raise ValueError(f"Duplicate package detected: {normalized}")

        pkg_version = dist.metadata.get("Version")

        if not pkg_version:
            raise ValueError(f"Package {name} does not have a Version metadata field.")

        packages[normalized] = pkg_version

    return packages


def get_own_version() -> str:
    """Get the version of ai-tools-base itself."""
    pkg_version = version("ai-tools-base")

    if not pkg_version:
        raise ValueError("ai-tools-base package does not have a Version metadata field.")

    return pkg_version


def try_parse_base_version(version_string: str) -> tuple[int, int, int] | None:
    """Try to extract major.minor.patch from a version string.

    Returns None if the version cannot be parsed as x.x.x format.
    """
    # Remove local version identifier (+...)
    version_string = version_string.split("+")[0]
    # Remove pre/post/dev suffixes (.dev1, .post1, etc)
    version_string = re.split(r"\.(dev|post|a|b|rc)", version_string)[0]
    # Parse major.minor.patch
    parts = version_string.split(".")
    if len(parts) < 3:
        raise ValueError("Version string does not have three parts.")

    try:
        return (int(parts[0]), int(parts[1]), int(parts[2]))
    except ValueError as err:
        raise ValueError("Version parts are not integers.") from err


def check_version_compatibility() -> bool:
    """Check that all ai-tools-* packages have the same version string.

    Returns:
        True if compatible, False otherwise.

    Emits:
        UserWarning: If versions are incompatible, with instructions to fix.
    """
    packages = get_ai_tools_packages()

    if len(packages) <= 1:
        return True

    # Simple string comparison - all versions must be identical
    unique_versions = set(packages.values())

    if len(unique_versions) <= 1:
        return True

    # Try to find highest version for upgrade suggestion
    highest_base: tuple[int, int, int] | None = None
    for ver in unique_versions:
        try:
            parsed = try_parse_base_version(ver)
            if parsed and (highest_base is None or parsed > highest_base):
                highest_base = parsed
        except ValueError:
            # Skip unparseable versions
            continue

    # Build warning message
    version_info = "\n".join(f"  - {name}: {ver}" for name, ver in sorted(packages.items()))

    if highest_base:
        highest_base_str = ".".join(map(str, highest_base))
        pkg_list = " ".join(f'"{name}>={highest_base_str}"' for name in sorted(packages))
        fix_msg = f"\n\nTo fix, run one of:\n  uv sync --reinstall\n  pip install --upgrade {pkg_list}"
    else:
        fix_msg = "\n\nTo fix, run:\n  uv sync --reinstall"

    warnings.warn(
        f"Incompatible ai-tools package versions!\n\n"
        f"Installed:\n{version_info}\n\n"
        f"All ai-tools-* packages must have the same version.{fix_msg}",
        UserWarning,
        stacklevel=2,
    )

    return False


def get_version_info() -> dict[str, str]:
    """Get version information for all ai-tools packages."""
    return get_ai_tools_packages()
