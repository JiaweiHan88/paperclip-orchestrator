"""Hatch build hook to pin ai_tools_* dependencies to the current build version.

This hook ensures that when building a package (e.g., ai-tools-github==1.2.0),
all ai_tools_* dependencies are pinned to the same version (e.g., ai_tools_base==1.2.0).

This prevents version mismatches when installing older versions of packages,
where pip would otherwise resolve unpinned dependencies to their latest versions.

Usage:
    Copy hatch_build.py to your package directory and add to pyproject.toml:

    [tool.hatch.build.hooks.custom]
    path = "hatch_build.py"
"""

import re

from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class AiToolsVersionPinHook(BuildHookInterface):
    """Hatch build hook to pin ai_tools_* dependencies to the current version."""

    PLUGIN_NAME = "ai_tools_version_pin"

    def initialize(self, version: str, build_data: dict) -> None:  # type: ignore[type-arg]
        """Pin ai_tools_* dependencies to match the version being built.

        Args:
            version: The version string being built (from uv-dynamic-versioning).
            build_data: Mutable dict containing build metadata including dependencies.
        """
        # Get the actual version from the build config
        actual_version = self.build_config.builder.metadata.version

        # Extract base version (major.minor.patch) for pinning
        # Handle versions like "1.2.3", "1.2.3+local", "1.2.3.dev1", etc.
        base_version = actual_version.split("+")[0]
        base_version = re.split(r"\.(dev|post|a|b|rc)", base_version)[0]

        # Get the core dependencies from the project metadata
        core = self.build_config.builder.metadata.core

        # Modify the dependencies in place
        new_deps = []
        for dep in core.dependencies:
            dep_normalized = dep.lower().replace("-", "_")
            # Check if this is an ai_tools package without a version specifier
            if dep_normalized.startswith("ai_tools_") and not any(
                op in dep for op in [">=", "<=", "==", "!=", ">", "<", "~="]
            ):
                # Replace with pinned version
                new_deps.append(f"{dep}=={base_version}")
            else:
                new_deps.append(dep)

        # Replace the dependencies list (using internal attribute)
        core._dependencies = new_deps
