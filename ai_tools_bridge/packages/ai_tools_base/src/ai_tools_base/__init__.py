"""Base interfaces and utilities for AI tools across different frameworks.

This package provides the foundational components needed to build AI tools that can
work across multiple frameworks and implementations. It includes abstract interfaces
for LLMs, language models, metrics collection, and logging, as well as utilities
for tool description and validation.

The package is designed to enable framework-agnostic AI tool development, allowing
tools to be written once and used with different AI frameworks through dependency
injection of the appropriate interface implementations.
"""

from .auth import get_token
from .interfaces import (
    EmbeddingInterface,
    LLMInterface,
    LoggingInterface,
    LogLevel,
    MetricsInterface,
    TSchema,
)
from .model import (
    InterfaceParameterNames,
    PostProcessor,
    RiskLevel,
    ToolDescription,
    WrappingValidationResult,
    wrap_tool_variable_with_selection,
)

# from .version_check import (
#    check_version_compatibility,
# )

# check_version_compatibility()

__all__ = [
    "LLMInterface",
    "TSchema",
    "EmbeddingInterface",
    "MetricsInterface",
    "LoggingInterface",
    "LogLevel",
    "ToolDescription",
    "WrappingValidationResult",
    "InterfaceParameterNames",
    "get_token",
    "RiskLevel",
    "PostProcessor",
    "wrap_tool_variable_with_selection",
]
