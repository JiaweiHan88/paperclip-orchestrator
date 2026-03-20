"""
Tool registry: auto-discovers all ToolDescription instances from every
ai_tools_* package and organises them by package slug.

Each package's ``tools.py`` module exposes module-level variables whose names
start with ``tool_`` and whose values are ``ToolDescription`` instances.

The registry is built once at process startup and is immutable thereafter.
"""

from __future__ import annotations

import importlib
import inspect
from dataclasses import dataclass, field
from types import ModuleType
from typing import Any

from ai_tools_base import RiskLevel, ToolDescription

# ---------------------------------------------------------------------------
# Package → module path mapping
# ---------------------------------------------------------------------------

PACKAGE_MODULES: dict[str, str] = {
    "github": "ai_tools_github.tools",
    "jira": "ai_tools_jira.tools",
    "confluence": "ai_tools_confluence.tools",
    "gerrit": "ai_tools_gerrit.tools",
}


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class BridgeToolEntry:
    """A single tool ready to be served by the bridge."""

    package: str
    name: str
    display_name: str
    description: str
    parameters_schema: dict[str, Any]
    risk_level: str  # "low" | "medium" | "high"
    _tool: ToolDescription = field(repr=False)

    @property
    def full_name(self) -> str:
        return f"{self.package}.{self.name}"


def _risk_level_to_str(level: RiskLevel) -> str:
    return level.value.lower()


def _load_tools_from_module(package: str, module: ModuleType) -> list[BridgeToolEntry]:
    entries: list[BridgeToolEntry] = []
    for attr_name, obj in inspect.getmembers(module):
        if not attr_name.startswith("tool_"):
            continue
        if not isinstance(obj, ToolDescription):
            continue

        tool_name = obj.name  # the canonical kebab-case name on ToolDescription
        schema = obj.args_schema.model_json_schema() if obj.args_schema is not None else {"type": "object", "properties": {}}

        entries.append(
            BridgeToolEntry(
                package=package,
                name=tool_name,
                display_name=obj.display_name if hasattr(obj, "display_name") and obj.display_name else _name_to_title(tool_name),
                description=obj.description or "",
                parameters_schema=schema,
                risk_level=_risk_level_to_str(obj.risk_level),
                _tool=obj,
            )
        )
    return entries


def _name_to_title(name: str) -> str:
    """Convert kebab-case tool name to a human-readable title."""
    return " ".join(word.capitalize() for word in name.replace("-", " ").split())


# ---------------------------------------------------------------------------
# Registry singleton
# ---------------------------------------------------------------------------


class ToolRegistry:
    """Holds all discovered tools, indexed by package and tool name."""

    def __init__(self) -> None:
        self._by_package: dict[str, dict[str, BridgeToolEntry]] = {}
        self._all: list[BridgeToolEntry] = []

    def load(self) -> None:
        """Import all tool modules and populate the registry."""
        for package, module_path in PACKAGE_MODULES.items():
            try:
                module = importlib.import_module(module_path)
            except ImportError as exc:
                # Log and skip packages that aren't installed / importable
                import logging
                logging.getLogger(__name__).warning(
                    "Could not import %s for package %s: %s", module_path, package, exc
                )
                self._by_package[package] = {}
                continue

            entries = _load_tools_from_module(package, module)
            self._by_package[package] = {e.name: e for e in entries}
            self._all.extend(entries)

    # ------------------------------------------------------------------
    # Public query API
    # ------------------------------------------------------------------

    def all_tools(self) -> list[BridgeToolEntry]:
        return list(self._all)

    def tools_for_package(self, package: str) -> list[BridgeToolEntry]:
        return list(self._by_package.get(package, {}).values())

    def get_tool(self, package: str, name: str) -> BridgeToolEntry | None:
        return self._by_package.get(package, {}).get(name)

    def packages(self) -> list[str]:
        return list(self._by_package.keys())


# Module-level singleton — loaded once when the server starts
registry = ToolRegistry()
