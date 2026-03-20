# AI Tools Base

Framework-agnostic base package for defining AI tools that can be converted to any AI framework (FastMCP, LangChain, LangGraph, etc.).

## Overview

Every AI framework requires tool definitions with common elements: an ID, description, input/output schemas, and an implementation function. This package provides a **unified, framework-agnostic tool description** that can be converted to framework-specific formats using companion packages.

### Key Features

- **Unified Tool Model** – Define tools once, use with any framework
- **Generic Interfaces** – Abstract LLM, embedding, metrics, and logging for dependency injection
- **Async Support** – All interfaces support both sync and async operations
- **Flexible Authentication** – Token retrieval from environment variables or netrc

## Installation

```bash
uv add ai-tools-base
```

## Core Components

### ToolDescription

The central model for defining AI tools:

```python
from pydantic import BaseModel
from ai_tools_base import ToolDescription, LLMInterface

class SearchInput(BaseModel):
    query: str
    max_results: int = 10

def search_tool(query: str, max_results: int, llm: LLMInterface) -> str:
    """Search and summarize results using an LLM."""
    results = perform_search(query, max_results)
    return llm.invoke(f"Summarize: {results}")

# Create tool description
tool = ToolDescription.from_func(search_tool, SearchInput)
```

| Field | Type | Description |
|-------|------|-------------|
| `name` | `str` | Tool identifier |
| `description` | `str` | Tool description (auto-extracted from docstring) |
| `args_schema` | `type[BaseModel]` | Pydantic model defining input parameters |
| `func` | `Callable` | The implementation function |

### Interfaces

Abstract interfaces enable dependency injection of framework-specific implementations:

| Interface | Purpose | Key Methods |
|-----------|---------|-------------|
| `LLMInterface` | LLM interactions | `invoke(prompt)`, `invoke_schema(prompt, schema)` |
| `EmbeddingInterface` | Text embeddings | `encode(text)`, `encode_many(texts)` |
| `MetricsInterface` | Metrics collection | `record(name, value)` |
| `LoggingInterface` | Logging & progress | `log(message)`, `report_progress(current, total)` |

Functions can declare interface parameters, which are automatically detected and injected by the target framework:

```python
def my_tool(query: str, llm: LLMInterface, logging: LoggingInterface) -> str:
    logging.info("Processing query...")
    return llm.invoke(query)
```

## Authentication

Retrieve tokens from environment variables or `~/.netrc`:

```python
from ai_tools_base import get_token

# Check env var first, then netrc
token = get_token(common_names="GITHUB_TOKEN")

# Different names for env vars and netrc hosts
token = get_token(
    env_names=["ZUUL_TOKEN", "ZUUL_AUTH_TOKEN"],
    netrc_names=["zuul.example.com"]
)
```

Environment variables take priority over netrc entries.

## Related Packages

This package is part of a larger ecosystem. Companion packages convert `ToolDescription` to specific frameworks:

- **ai-tools-to-mcp** – Convert to FastMCP tools
- **ai-tools-to-langgraph** – Convert to LangChain tools
