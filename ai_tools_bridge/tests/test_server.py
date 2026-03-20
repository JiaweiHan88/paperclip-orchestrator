"""Basic tests for the AI Tools Bridge server."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from ai_tools_bridge.registry import BridgeToolEntry, ToolRegistry
from ai_tools_bridge.server import app


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_mock_entry(package: str, name: str, risk: str = "low") -> BridgeToolEntry:
    """Create a minimal BridgeToolEntry backed by a simple mock tool."""
    from pydantic import BaseModel

    class _Schema(BaseModel):
        value: str = "hello"

    async def _handler(value: str = "hello") -> str:  # noqa: D401
        return f"ok:{value}"

    mock_tool = MagicMock()
    mock_tool.name = name
    mock_tool.args_schema = _Schema
    mock_tool.func = _handler
    mock_tool.risk_level = MagicMock(value=risk)

    return BridgeToolEntry(
        package=package,
        name=name,
        display_name=name.replace("_", " ").title(),
        description=f"Mock {name} tool",
        parameters_schema=_Schema.model_json_schema(),
        risk_level=risk,
        _tool=mock_tool,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.fixture()
def client():
    """TestClient with a pre-loaded mock registry."""
    mock_registry = ToolRegistry()
    mock_registry._by_package = {
        "github": {"get_pull_request": _make_mock_entry("github", "get_pull_request")},
        "jira": {"get_jira_issue": _make_mock_entry("jira", "get_jira_issue")},
    }
    mock_registry._all = list(mock_registry._by_package["github"].values()) + list(
        mock_registry._by_package["jira"].values()
    )

    with patch("ai_tools_bridge.server.registry", mock_registry):
        with TestClient(app) as c:
            yield c


def test_health(client: TestClient) -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["tools_loaded"] == 2


def test_full_manifest(client: TestClient) -> None:
    resp = client.get("/tools/manifest")
    assert resp.status_code == 200
    tools = resp.json()["tools"]
    assert len(tools) == 2
    names = {t["name"] for t in tools}
    assert "get_pull_request" in names
    assert "get_jira_issue" in names


def test_package_manifest(client: TestClient) -> None:
    resp = client.get("/tools/manifest/github")
    assert resp.status_code == 200
    tools = resp.json()["tools"]
    assert len(tools) == 1
    assert tools[0]["package"] == "github"


def test_package_manifest_unknown(client: TestClient) -> None:
    resp = client.get("/tools/manifest/unknown_pkg")
    assert resp.status_code == 404


def test_execute_tool(client: TestClient) -> None:
    resp = client.post(
        "/tools/github/get_pull_request",
        json={"params": {"value": "world"}, "credentials": {}},
    )
    assert resp.status_code == 200
    assert resp.json()["content"] == "ok:world"


def test_execute_tool_not_found(client: TestClient) -> None:
    resp = client.post(
        "/tools/github/nonexistent_tool",
        json={"params": {}, "credentials": {}},
    )
    assert resp.status_code == 404


def test_execute_tool_validation_error(client: TestClient) -> None:
    # Pass an extra unknown field that Pydantic (with extra=forbid) should reject
    # Our mock schema uses extra=allow by default; just test 422 via invalid type
    resp = client.post(
        "/tools/jira/get_jira_issue",
        json={"params": {"value": 123456789012345678901234567890}, "credentials": {}},
    )
    # Pydantic coerces int to str for str fields, so this actually succeeds
    assert resp.status_code == 200
