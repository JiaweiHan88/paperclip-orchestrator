"""Tests for async function detection in ToolDescription wrapping validation."""

import asyncio
import inspect
from typing import Any

from pydantic import BaseModel

from ai_tools_base import (
    EmbeddingInterface,
    LLMInterface,
    LoggingInterface,
    LogLevel,
    MetricsInterface,
    RiskLevel,
    ToolDescription,
)


class TestAsyncDetection:
    """Test async function detection in wrapping validation."""

    def test_sync_function_detection(self) -> None:
        """Test that sync functions are correctly identified as not async."""

        class TestSchema(BaseModel):
            text: str

        def sync_function(text: str) -> str:
            """A synchronous test function."""
            return f"processed: {text}"

        tool = ToolDescription(
            name="sync_tool",
            description="A sync tool for testing",
            risk_level=RiskLevel.LOW,
            args_schema=TestSchema,
            func=sync_function,
        )

        result = tool.wrapping_validation()

        assert inspect.iscoroutinefunction(result.func) is False
        assert list(result.args_schema.model_fields.keys()) == ["text"]
        assert result.interface_parameter_names.llm == []
        assert result.interface_parameter_names.embedding == []
        assert result.interface_parameter_names.metrics == []
        assert result.interface_parameter_names.logging == []

    def test_async_function_detection(self) -> None:
        """Test that async functions are correctly identified as async."""

        class TestSchema(BaseModel):
            text: str

        async def async_function(text: str) -> str:
            """An asynchronous test function."""
            await asyncio.sleep(0.001)  # Small async operation
            return f"async processed: {text}"

        tool = ToolDescription(
            name="async_tool",
            description="An async tool for testing",
            risk_level=RiskLevel.LOW,
            args_schema=TestSchema,
            func=async_function,
        )

        result = tool.wrapping_validation()

        assert inspect.iscoroutinefunction(result.func) is True
        assert list(result.args_schema.model_fields.keys()) == ["text"]
        assert result.interface_parameter_names.llm == []
        assert result.interface_parameter_names.embedding == []
        assert result.interface_parameter_names.metrics == []
        assert result.interface_parameter_names.logging == []

    def test_sync_function_with_interfaces(self) -> None:
        """Test sync function detection with LLM and logging interfaces."""

        class TestSchema(BaseModel):
            query: str

        def sync_function_with_interfaces(query: str, llm: LLMInterface, logger: LoggingInterface) -> str:
            """A sync function that uses interfaces."""
            return f"query: {query}"

        tool = ToolDescription(
            name="sync_tool_with_interfaces",
            description="Sync tool with interfaces",
            risk_level=RiskLevel.LOW,
            args_schema=TestSchema,
            func=sync_function_with_interfaces,
        )

        result = tool.wrapping_validation()

        assert inspect.iscoroutinefunction(result.func) is False
        assert list(result.args_schema.model_fields.keys()) == ["query"]
        assert result.interface_parameter_names.llm == ["llm"]
        assert result.interface_parameter_names.logging == ["logger"]

    def test_async_function_with_interfaces(self) -> None:
        """Test async function detection with LLM and logging interfaces."""

        class TestSchema(BaseModel):
            query: str

        async def async_function_with_interfaces(query: str, llm: LLMInterface, logger: LoggingInterface) -> str:
            """An async function that uses interfaces."""
            logger.log(f"Processing query: {query}", LogLevel.INFO)
            response = await llm.ainvoke(f"Process this: {query}")
            return response

        tool = ToolDescription(
            name="async_tool_with_interfaces",
            description="Async tool with interfaces",
            risk_level=RiskLevel.LOW,
            args_schema=TestSchema,
            func=async_function_with_interfaces,
        )

        result = tool.wrapping_validation()

        assert inspect.iscoroutinefunction(result.func) is True
        assert list(result.args_schema.model_fields.keys()) == ["query"]
        assert result.interface_parameter_names.llm == ["llm"]
        assert result.interface_parameter_names.logging == ["logger"]

    def test_async_function_with_constants(self) -> None:
        """Test async function detection with constant interface overrides."""

        class MockLLM(LLMInterface):
            def invoke(self, prompt: str) -> str:
                return f"mock response: {prompt}"

            async def ainvoke(self, prompt: str) -> str:
                return f"async mock response: {prompt}"

            def invoke_schema(self, prompt: str, schema: type[Any]) -> Any:
                return schema(message="mock")

            async def ainvoke_schema(self, prompt: str, schema: type[Any]) -> Any:
                return schema(message="async mock")

        class MockLM(EmbeddingInterface):
            def encode(self, text: str) -> list[float]:
                # Return a deterministic dummy embedding
                return [0.0]

            def encode_batch(self, texts: list[str]) -> list[list[float]]:
                # Return a deterministic dummy embedding per input
                return [[0.0] for _ in texts]

        class MockMetrics(MetricsInterface):
            def add(self, name: str, value: Any) -> None:  # noqa: D401 - simple stub
                # No-op metrics collection for testing
                pass

        class MockLogger(LoggingInterface):
            def report_progress(self, current: int, total: int, message: str) -> None:
                pass

            async def areport_progress(self, current: int, total: int, message: str) -> None:
                pass

            def log(self, message: str, level: LogLevel | None = None) -> None:
                pass

            async def alog(self, message: str, level: LogLevel | None = None) -> None:
                pass

        class TestSchema(BaseModel):
            text: str

        async def async_function_with_constants(
            text: str,
            llm: LLMInterface,
            logger: LoggingInterface,
        ) -> str:
            """Async function with constant interfaces provided."""
            logger.log(f"Processing: {text}")
            return await llm.ainvoke(f"Transform: {text}")

        tool = ToolDescription(
            name="async_tool_constants",
            description="Async tool with constants",
            risk_level=RiskLevel.LOW,
            args_schema=TestSchema,
            func=async_function_with_constants,
        )

        constants = {
            "llm": MockLLM(),
            "lm": MockLM(),
            "metrics": MockMetrics(),
            "logger": MockLogger(),
        }

        result = tool.wrapping_validation(constants)

        assert inspect.iscoroutinefunction(result.func) is True
        assert list(result.args_schema.model_fields.keys()) == ["text"]
        assert result.interface_parameter_names.llm == []  # Provided by constants
        assert result.interface_parameter_names.embedding == []  # Provided by constants
        assert result.interface_parameter_names.metrics == []  # Provided by constants
        assert result.interface_parameter_names.logging == []  # Provided by constants

    def test_lambda_function_sync(self) -> None:
        """Test detection with sync lambda function."""

        class TestSchema(BaseModel):
            value: int

        def sync_lambda(value: int) -> int:
            return value * 2

        tool = ToolDescription(
            name="lambda_sync",
            description="Sync lambda tool",
            risk_level=RiskLevel.LOW,
            args_schema=TestSchema,
            func=sync_lambda,
        )

        result = tool.wrapping_validation()

        assert inspect.iscoroutinefunction(result.func) is False
        assert list(result.args_schema.model_fields.keys()) == ["value"]

    def test_class_method_async(self) -> None:
        """Test detection with async class method."""

        class TestProcessor:
            async def process(self, data: str) -> str:
                """Async method for processing data."""
                await asyncio.sleep(0.001)
                return f"processed: {data}"

        class TestSchema(BaseModel):
            data: str

        processor = TestProcessor()

        tool = ToolDescription(
            name="method_async",
            description="Async method tool",
            risk_level=RiskLevel.LOW,
            args_schema=TestSchema,
            func=processor.process,
        )

        result = tool.wrapping_validation()

        assert inspect.iscoroutinefunction(result.func) is True
        assert list(result.args_schema.model_fields.keys()) == ["data"]
