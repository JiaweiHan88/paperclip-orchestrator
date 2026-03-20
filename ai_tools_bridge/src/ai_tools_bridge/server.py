"""
FastAPI bridge server that exposes all ai_tools_* tool functions over HTTP.

Endpoints
---------
GET  /health                     → health check
GET  /tools/manifest             → full tool manifest (all packages)
GET  /tools/manifest/{package}   → per-package manifest
POST /tools/{package}/{tool_name} → execute a tool
"""

from __future__ import annotations

import asyncio
import inspect
import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ValidationError

from .registry import registry

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Lifespan: load registry once at startup
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI):  # type: ignore[type-arg]
    registry.load()
    loaded = len(registry.all_tools())
    logger.info("ai_tools_bridge ready — %d tools loaded", loaded)
    yield


app = FastAPI(
    title="AI Tools Bridge",
    description="HTTP bridge exposing ai_tools_* packages for Paperclip plugin workers",
    version="0.1.0",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------


class ToolExecuteRequest(BaseModel):
    """Payload for a tool execution request.

    ``params`` is passed verbatim to the tool function after Pydantic validation
    against the tool's ``args_schema``.

    ``credentials`` carries per-request auth config so the bridge stays
    stateless: no credentials are persisted between requests.
    """

    params: dict[str, Any] = {}
    credentials: dict[str, Any] = {}


class ToolManifestEntry(BaseModel):
    package: str
    name: str
    full_name: str
    display_name: str
    description: str
    parameters_schema: dict[str, Any]
    risk_level: str


class ToolManifestResponse(BaseModel):
    tools: list[ToolManifestEntry]


class ToolExecuteResponse(BaseModel):
    content: str | None = None
    data: Any = None
    error: str | None = None


# ---------------------------------------------------------------------------
# Helper: call a tool function (sync or async) safely
# ---------------------------------------------------------------------------


async def _invoke_tool(entry: Any, params: dict[str, Any], credentials: dict[str, Any]) -> Any:
    """Validate params with the tool's Pydantic schema and call the handler.

    Credentials are injected into the call kwargs if the function signature
    accepts a matching parameter name (e.g. ``token``, ``username`` …).
    """
    tool = entry._tool

    # Validate and coerce inputs via the tool's args_schema
    try:
        validated = tool.args_schema(**params)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.errors()) from exc

    # Build kwargs from the validated model
    kwargs: dict[str, Any] = validated.model_dump()

    # Inject credentials whose names match function parameters that are NOT
    # in the schema (i.e. injected at runtime).
    sig = inspect.signature(tool.func)
    schema_field_names = set(tool.args_schema.model_fields.keys())
    for cred_key, cred_val in credentials.items():
        if cred_key in sig.parameters and cred_key not in schema_field_names:
            kwargs[cred_key] = cred_val

    try:
        if inspect.iscoroutinefunction(tool.func):
            result = await tool.func(**kwargs)
        else:
            result = await asyncio.get_event_loop().run_in_executor(None, lambda: tool.func(**kwargs))
    except Exception as exc:
        logger.exception("Tool %s.%s raised an exception", entry.package, entry.name)
        return ToolExecuteResponse(error=str(exc))

    # Normalise result to ToolExecuteResponse
    if isinstance(result, str):
        return ToolExecuteResponse(content=result)
    if isinstance(result, dict):
        return ToolExecuteResponse(data=result)
    if result is None:
        return ToolExecuteResponse(content="")
    # For any other type, serialise to string
    return ToolExecuteResponse(content=str(result))


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.get("/health")
async def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "tools_loaded": len(registry.all_tools()),
        "packages": registry.packages(),
    }


def _entry_to_manifest(entry: Any) -> ToolManifestEntry:
    return ToolManifestEntry(
        package=entry.package,
        name=entry.name,
        full_name=entry.full_name,
        display_name=entry.display_name,
        description=entry.description,
        parameters_schema=entry.parameters_schema,
        risk_level=entry.risk_level,
    )


@app.get("/tools/manifest", response_model=ToolManifestResponse)
async def get_full_manifest() -> ToolManifestResponse:
    """Return the manifest of all tools across all packages."""
    return ToolManifestResponse(tools=[_entry_to_manifest(e) for e in registry.all_tools()])


@app.get("/tools/manifest/{package}", response_model=ToolManifestResponse)
async def get_package_manifest(package: str) -> ToolManifestResponse:
    """Return the manifest for a single package."""
    tools = registry.tools_for_package(package)
    if not tools and package not in registry.packages():
        raise HTTPException(status_code=404, detail=f"Unknown package: {package}")
    return ToolManifestResponse(tools=[_entry_to_manifest(e) for e in tools])


@app.post("/tools/{package}/{tool_name}", response_model=ToolExecuteResponse)
async def execute_tool(package: str, tool_name: str, body: ToolExecuteRequest) -> ToolExecuteResponse:
    """Execute a single tool by package and name."""
    entry = registry.get_tool(package, tool_name)
    if entry is None:
        raise HTTPException(
            status_code=404,
            detail=f"Tool '{tool_name}' not found in package '{package}'",
        )
    return await _invoke_tool(entry, body.params, body.credentials)
