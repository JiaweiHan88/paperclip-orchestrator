import pytest
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
from ai_tools_base.func_signature import SignatureValidationError
from ai_tools_base.interfaces import TSchema


class TestLLMInterface:
    """Test cases for the LLMInterface abstract base class."""

    def test_cannot_instantiate_llm_interface_directly(self):
        """LLMInterface is abstract and should not be instantiated directly."""
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            LLMInterface()  # type: ignore[abstract]

    def test_concrete_implementation_methods(self):
        """Test that concrete implementation methods work as expected."""

        class MockLLM(LLMInterface):
            def invoke(self, prompt: str) -> str:
                return f"Mock response for: {prompt}"

            async def ainvoke(self, prompt: str) -> str:
                return f"Async mock response for: {prompt}"

            def invoke_schema(self, prompt: str, schema: type[TSchema]) -> TSchema:
                # Mock implementation that creates a valid instance
                return schema(name="Mock Name", value=42)

            async def ainvoke_schema(self, prompt: str, schema: type[TSchema]) -> TSchema:
                # Mock implementation that creates a valid instance
                return schema(name="Async Mock Name", value=84)

        llm = MockLLM()
        assert isinstance(llm, LLMInterface)

        # Test invoke
        result = llm.invoke("test prompt")
        assert result == "Mock response for: test prompt"

        # Test invoke_schema
        class TestSchema(BaseModel):
            name: str
            value: int

        schema_result: TestSchema = llm.invoke_schema("extract data", TestSchema)
        assert isinstance(schema_result, TestSchema)
        assert schema_result.name == "Mock Name"
        assert schema_result.value == 42

    def test_concrete_implementation_must_implement_invoke_schema(self):
        """Test that concrete implementations must implement invoke_schema."""

        class IncompleteMLLM(LLMInterface):
            def invoke(self, prompt: str) -> str:
                return "response"

            # Missing invoke_schema implementation

        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            IncompleteMLLM()  # type: ignore[abstract]

    def test_invoke_schema_type_safety(self):
        """Test that invoke_schema respects type bounds."""

        class MockLLM(LLMInterface):
            def invoke(self, prompt: str) -> str:
                return "response"

            async def ainvoke(self, prompt: str) -> str:
                return "async response"

            def invoke_schema(self, prompt: str, schema: type[TSchema]) -> TSchema:
                return schema(test_field="value")  # type: ignore

            async def ainvoke_schema(self, prompt: str, schema: type[TSchema]) -> TSchema:
                return schema(test_field="async value")  # type: ignore

        class TestSchema(BaseModel):
            test_field: str

        llm = MockLLM()
        result = llm.invoke_schema("test", TestSchema)

        # Should return an instance of the schema type
        assert isinstance(result, TestSchema)
        assert result.test_field == "value"

    @pytest.mark.asyncio
    async def test_ainvoke_method(self):
        """Test that the async ainvoke method works correctly."""

        class MockLLM(LLMInterface):
            def invoke(self, prompt: str) -> str:
                return f"Sync: {prompt}"

            async def ainvoke(self, prompt: str) -> str:
                return f"Async: {prompt}"

            def invoke_schema(self, prompt: str, schema: type[TSchema]) -> TSchema:
                return schema(message="sync")  # type: ignore

            async def ainvoke_schema(self, prompt: str, schema: type[TSchema]) -> TSchema:
                return schema(message="async")  # type: ignore

        llm = MockLLM()
        result = await llm.ainvoke("test prompt")
        assert result == "Async: test prompt"

    @pytest.mark.asyncio
    async def test_ainvoke_schema_method(self):
        """Test that the async ainvoke_schema method works correctly."""

        class TestSchema(BaseModel):
            message: str
            count: int = 0

        class MockLLM(LLMInterface):
            def invoke(self, prompt: str) -> str:
                return "sync response"

            async def ainvoke(self, prompt: str) -> str:
                return "async response"

            def invoke_schema(self, prompt: str, schema: type[TSchema]) -> TSchema:
                return schema(message="sync", count=1)  # type: ignore

            async def ainvoke_schema(self, prompt: str, schema: type[TSchema]) -> TSchema:
                return schema(message="async", count=2)  # type: ignore

        llm = MockLLM()
        result = await llm.ainvoke_schema("extract data", TestSchema)

        assert isinstance(result, TestSchema)
        assert result.message == "async"
        assert result.count == 2


class TestLoggingInterface:
    """Test cases for the LoggingInterface abstract base class."""

    def test_cannot_instantiate_logging_interface_directly(self):
        """LoggingInterface is abstract and should not be instantiated directly."""
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            LoggingInterface()  # type: ignore[abstract]

    def test_concrete_implementation_methods(self):
        """Test that concrete implementation methods work as expected."""

        class MockLogging(LoggingInterface):
            def __init__(self) -> None:
                self.progress_calls: list[tuple[int, int, str]] = []
                self.log_calls: list[tuple[str, LogLevel]] = []

            def report_progress(self, current: int, total: int, message: str) -> None:
                self.progress_calls.append((current, total, message))

            async def areport_progress(self, current: int, total: int, message: str) -> None:
                self.progress_calls.append((current, total, message))

            def log(self, message: str, level: LogLevel | None = None) -> None:
                if level is None:
                    level = LogLevel.INFO
                self.log_calls.append((message, level))

            async def alog(self, message: str, level: LogLevel | None = None) -> None:
                if level is None:
                    level = LogLevel.INFO
                self.log_calls.append((message, level))

        logging_interface = MockLogging()
        assert isinstance(logging_interface, LoggingInterface)

        # Test report_progress
        logging_interface.report_progress(5, 10, "Processing...")
        assert logging_interface.progress_calls == [(5, 10, "Processing...")]

    @pytest.mark.asyncio
    async def test_async_logging_methods(self):
        """Test that async logging methods work correctly."""

        class MockLogging(LoggingInterface):
            def __init__(self) -> None:
                self.progress_calls: list[tuple[int, int, str, str]] = []  # Added type marker
                self.log_calls: list[tuple[str, LogLevel, str]] = []  # Added type marker

            def report_progress(self, current: int, total: int, message: str) -> None:
                self.progress_calls.append((current, total, message, "sync"))

            async def areport_progress(self, current: int, total: int, message: str) -> None:
                self.progress_calls.append((current, total, message, "async"))

            def log(self, message: str, level: LogLevel | None = None) -> None:
                if level is None:
                    level = LogLevel.INFO
                self.log_calls.append((message, level, "sync"))

            async def alog(self, message: str, level: LogLevel | None = None) -> None:
                if level is None:
                    level = LogLevel.INFO
                self.log_calls.append((message, level, "async"))

        logging_interface = MockLogging()

        # Test async report_progress
        await logging_interface.areport_progress(3, 7, "Async processing...")
        assert logging_interface.progress_calls == [(3, 7, "Async processing...", "async")]

        # Test async log with default level
        await logging_interface.alog("Async log message")
        assert logging_interface.log_calls == [("Async log message", LogLevel.INFO, "async")]

        # Test async log with specific level
        await logging_interface.alog("Async error message", LogLevel.ERROR)
        expected_calls = [
            ("Async log message", LogLevel.INFO, "async"),
            ("Async error message", LogLevel.ERROR, "async"),
        ]
        assert logging_interface.log_calls == expected_calls

    @pytest.mark.asyncio
    async def test_mixed_sync_async_logging(self):
        """Test that both sync and async methods can be used together."""

        class MockLogging(LoggingInterface):
            def __init__(self) -> None:
                self.all_calls: list[str] = []

            def report_progress(self, current: int, total: int, message: str) -> None:
                self.all_calls.append(f"sync_progress: {current}/{total} - {message}")

            async def areport_progress(self, current: int, total: int, message: str) -> None:
                self.all_calls.append(f"async_progress: {current}/{total} - {message}")

            def log(self, message: str, level: LogLevel | None = None) -> None:
                level_str = level.value if level else LogLevel.INFO.value
                self.all_calls.append(f"sync_log: [{level_str}] {message}")

            async def alog(self, message: str, level: LogLevel | None = None) -> None:
                level_str = level.value if level else LogLevel.INFO.value
                self.all_calls.append(f"async_log: [{level_str}] {message}")

        logging_interface = MockLogging()

        # Mix sync and async calls
        logging_interface.report_progress(1, 5, "Step 1")
        await logging_interface.areport_progress(2, 5, "Step 2")
        logging_interface.log("Sync message")
        await logging_interface.alog("Async message", LogLevel.DEBUG)

        expected_calls = [
            "sync_progress: 1/5 - Step 1",
            "async_progress: 2/5 - Step 2",
            "sync_log: [INFO] Sync message",
            "async_log: [DEBUG] Async message",
        ]
        assert logging_interface.all_calls == expected_calls


class TestLoggingConvenienceMethods:
    """Test cases for LoggingInterface convenience methods for different log levels."""

    def test_sync_convenience_methods(self):
        """Test all sync convenience methods (debug, info, warning, error, critical).

        Requirements:
        - Each convenience method should call the base log() method with the correct LogLevel
        - Methods should be available on concrete implementations
        - Message content should be preserved
        """

        class MockLogging(LoggingInterface):
            def __init__(self) -> None:
                self.log_calls: list[tuple[str, LogLevel]] = []

            def report_progress(self, current: int, total: int, message: str) -> None:
                pass

            async def areport_progress(self, current: int, total: int, message: str) -> None:
                pass

            def log(self, message: str, level: LogLevel | None = None) -> None:
                if level is None:
                    level = LogLevel.INFO
                self.log_calls.append((message, level))

            async def alog(self, message: str, level: LogLevel | None = None) -> None:
                if level is None:
                    level = LogLevel.INFO
                self.log_calls.append((message, level))

        logging_interface = MockLogging()

        # Test all sync convenience methods
        logging_interface.debug("Debug message")
        logging_interface.info("Info message")
        logging_interface.warning("Warning message")
        logging_interface.error("Error message")
        logging_interface.critical("Critical message")

        expected_calls = [
            ("Debug message", LogLevel.DEBUG),
            ("Info message", LogLevel.INFO),
            ("Warning message", LogLevel.WARNING),
            ("Error message", LogLevel.ERROR),
            ("Critical message", LogLevel.CRITICAL),
        ]
        assert logging_interface.log_calls == expected_calls

    @pytest.mark.asyncio
    async def test_async_convenience_methods(self):
        """Test all async convenience methods (adebug, ainfo, awarning, aerror, acritical).

        Requirements:
        - Each async convenience method should call the base alog() method with the correct LogLevel
        - Methods should be awaitable
        - Message content should be preserved
        """

        class MockLogging(LoggingInterface):
            def __init__(self) -> None:
                self.log_calls: list[tuple[str, LogLevel, str]] = []

            def report_progress(self, current: int, total: int, message: str) -> None:
                pass

            async def areport_progress(self, current: int, total: int, message: str) -> None:
                pass

            def log(self, message: str, level: LogLevel | None = None) -> None:
                if level is None:
                    level = LogLevel.INFO
                self.log_calls.append((message, level, "sync"))

            async def alog(self, message: str, level: LogLevel | None = None) -> None:
                if level is None:
                    level = LogLevel.INFO
                self.log_calls.append((message, level, "async"))

        logging_interface = MockLogging()

        # Test all async convenience methods
        await logging_interface.adebug("Async debug message")
        await logging_interface.ainfo("Async info message")
        await logging_interface.awarning("Async warning message")
        await logging_interface.aerror("Async error message")
        await logging_interface.acritical("Async critical message")

        expected_calls = [
            ("Async debug message", LogLevel.DEBUG, "async"),
            ("Async info message", LogLevel.INFO, "async"),
            ("Async warning message", LogLevel.WARNING, "async"),
            ("Async error message", LogLevel.ERROR, "async"),
            ("Async critical message", LogLevel.CRITICAL, "async"),
        ]
        assert logging_interface.log_calls == expected_calls

    @pytest.mark.asyncio
    async def test_mixed_convenience_and_direct_methods(self):
        """Test using convenience methods alongside direct log() and alog() calls.

        Requirements:
        - Convenience methods and direct methods should work together seamlessly
        - All calls should be recorded in order
        - Both sync and async variants should work correctly
        """

        class MockLogging(LoggingInterface):
            def __init__(self) -> None:
                self.all_calls: list[str] = []

            def report_progress(self, current: int, total: int, message: str) -> None:
                pass

            async def areport_progress(self, current: int, total: int, message: str) -> None:
                pass

            def log(self, message: str, level: LogLevel | None = None) -> None:
                level_str = level.value if level else LogLevel.INFO.value
                self.all_calls.append(f"sync_log: [{level_str}] {message}")

            async def alog(self, message: str, level: LogLevel | None = None) -> None:
                level_str = level.value if level else LogLevel.INFO.value
                self.all_calls.append(f"async_log: [{level_str}] {message}")

        logging_interface = MockLogging()

        # Mix convenience methods with direct calls
        logging_interface.debug("Debug via convenience")
        logging_interface.log("Direct log call", LogLevel.INFO)
        await logging_interface.aerror("Error via async convenience")
        await logging_interface.alog("Direct async log call", LogLevel.WARNING)
        logging_interface.critical("Critical via convenience")

        expected_calls = [
            "sync_log: [DEBUG] Debug via convenience",
            "sync_log: [INFO] Direct log call",
            "async_log: [ERROR] Error via async convenience",
            "async_log: [WARNING] Direct async log call",
            "sync_log: [CRITICAL] Critical via convenience",
        ]
        assert logging_interface.all_calls == expected_calls

    def test_convenience_methods_with_special_characters(self):
        """Test convenience methods with various message formats including special characters.

        Requirements:
        - Methods should handle messages with newlines, unicode, and special formatting
        - Message content should be preserved exactly
        """

        class MockLogging(LoggingInterface):
            def __init__(self) -> None:
                self.log_calls: list[tuple[str, LogLevel]] = []

            def report_progress(self, current: int, total: int, message: str) -> None:
                pass

            async def areport_progress(self, current: int, total: int, message: str) -> None:
                pass

            def log(self, message: str, level: LogLevel | None = None) -> None:
                if level is None:
                    level = LogLevel.INFO
                self.log_calls.append((message, level))

            async def alog(self, message: str, level: LogLevel | None = None) -> None:
                if level is None:
                    level = LogLevel.INFO
                self.log_calls.append((message, level))

        logging_interface = MockLogging()

        # Test with various special characters and formatting
        logging_interface.debug("Debug with\nnewlines")
        logging_interface.info("Info with unicode: 🚀 émojis and àccents")
        logging_interface.warning("Warning with 'quotes' and \"double quotes\"")
        logging_interface.error("Error with\ttabs\tand\tspaces")
        logging_interface.critical('Critical with JSON: {"key": "value"}')

        expected_calls = [
            ("Debug with\nnewlines", LogLevel.DEBUG),
            ("Info with unicode: 🚀 émojis and àccents", LogLevel.INFO),
            ("Warning with 'quotes' and \"double quotes\"", LogLevel.WARNING),
            ("Error with\ttabs\tand\tspaces", LogLevel.ERROR),
            ('Critical with JSON: {"key": "value"}', LogLevel.CRITICAL),
        ]
        assert logging_interface.log_calls == expected_calls


class TestEmbeddingInterface:
    """Test cases for the EmbeddingInterface abstract base class."""

    def test_cannot_instantiate_lm_interface_directly(self):
        """EmbeddingInterface is abstract and should not be instantiated directly."""
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            EmbeddingInterface()  # type: ignore[abstract]

    @pytest.mark.asyncio
    async def test_concrete_implementation_methods(self):
        """Test that concrete implementation methods work as expected.

        Requirements:
        - encode returns a list[float]
        - encode_batch returns list[list[float]] sized to input batch
        """

        class MockLM(EmbeddingInterface):
            def encode(self, text: str) -> list[float]:  # pragma: no cover
                return [0.2, 0.4, 0.6]

            def encode_batch(self, texts: list[str]) -> list[list[float]]:  # pragma: no cover
                return [[0.2, 0.4, 0.6] for _ in texts]

        lm = MockLM()
        assert isinstance(lm, EmbeddingInterface)

        single = lm.encode("abc")
        assert single == [0.2, 0.4, 0.6]

        batch = lm.encode_batch(["a", "abcd"])
        assert batch == [[0.2, 0.4, 0.6], [0.2, 0.4, 0.6]]


class TestMetricsInterface:
    """Test cases for the MetricsInterface abstract base class."""

    def test_can_instantiate_metrics_interface_without_abstract_methods(self):
        """MetricsInterface currently HAS an abstract method and can't be instantiated.

        If the interface becomes concrete (no abstract methods) this expectation should
        be revisited and the test updated accordingly.
        """
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            MetricsInterface()  # type: ignore[abstract]

    @pytest.mark.asyncio
    async def test_concrete_implementation_add(self):
        """Test that a concrete metrics implementation collects metrics.

        Requirements:
        - add is awaited and records name/value pairs
        - multiple calls accumulate metrics
        """

        class MockMetrics(MetricsInterface):
            def __init__(self) -> None:
                self.data: list[tuple[str, float]] = []

            def add(self, name: str, value: float) -> None:  # type: ignore[override]
                self.data.append((name, value))

        metrics = MockMetrics()
        metrics.add("loss", 0.5)
        metrics.add("accuracy", 0.9)
        assert metrics.data == [("loss", 0.5), ("accuracy", 0.9)]


class TestToolDescription:
    """Test cases for the ToolDescription class and its wrapping_validation method."""

    def test_tool_description_creation(self):
        """ToolDescription should be created with all required fields."""

        class TestSchema(BaseModel):
            arg1: str
            arg2: int

        def test_func(arg1: str, arg2: int) -> str:
            return f"{arg1}_{arg2}"

        tool = ToolDescription(
            name="test_tool",
            description="A test tool",
            risk_level=RiskLevel.LOW,
            args_schema=TestSchema,
            func=test_func,
        )

        assert tool.name == "test_tool"
        assert tool.description == "A test tool"
        assert tool.args_schema == TestSchema
        assert tool.func == test_func

    def test_wrapping_validation_basic(self):
        """Test wrapping_validation with basic function parameters."""

        class TestSchema(BaseModel):
            name: str
            age: int

        def test_func(name: str, age: int) -> str:
            return f"{name} is {age}"

        tool = ToolDescription(
            name="test_tool",
            description="A test tool",
            args_schema=TestSchema,
            func=test_func,
            risk_level=RiskLevel.LOW,
        )

        result = tool.wrapping_validation()

        assert set(result.args_schema.model_fields.keys()) == {"name", "age"}
        assert result.interface_parameter_names.llm == []
        assert result.interface_parameter_names.embedding == []
        assert result.interface_parameter_names.metrics == []
        assert result.interface_parameter_names.logging == []

    def test_wrapping_validation_with_llm_interface(self):
        """Test wrapping_validation with LLMInterface parameter."""

        class TestSchema(BaseModel):
            prompt: str

        def test_func(prompt: str, llm: LLMInterface) -> str:
            return f"Processing {prompt}"

        tool = ToolDescription(
            name="test_tool",
            description="A test tool with LLM",
            args_schema=TestSchema,
            func=test_func,
            risk_level=RiskLevel.LOW,
        )

        result = tool.wrapping_validation()

        assert list(result.args_schema.model_fields.keys()) == ["prompt"]
        assert result.interface_parameter_names.llm == ["llm"]
        assert result.interface_parameter_names.embedding == []
        assert result.interface_parameter_names.metrics == []
        assert result.interface_parameter_names.logging == []

    def test_wrapping_validation_multiple_llm_interfaces(self):
        """Test wrapping_validation with multiple LLMInterface parameters."""

        class TestSchema(BaseModel):
            text: str

        def test_func(text: str, primary_llm: LLMInterface, secondary_llm: LLMInterface) -> str:
            return f"Processing {text}"

        tool = ToolDescription(
            name="test_tool",
            description="A test tool with multiple LLMs",
            args_schema=TestSchema,
            func=test_func,
            risk_level=RiskLevel.LOW,
        )

        result = tool.wrapping_validation()

        assert list(result.args_schema.model_fields.keys()) == ["text"]
        assert set(result.interface_parameter_names.llm) == {"primary_llm", "secondary_llm"}
        assert result.interface_parameter_names.embedding == []
        assert result.interface_parameter_names.metrics == []
        assert result.interface_parameter_names.logging == []

    def test_wrapping_validation_with_lm_interface(self):
        """Test wrapping_validation with EmbeddingInterface parameter.

        Requirements:
        - Detect lm parameter name
        - Recognize schema parameter annotations
        """

        class TestSchema(BaseModel):
            text: str

        def test_func(text: str, embedding: EmbeddingInterface) -> str:  # noqa: D401 - simple example
            return text

        tool = ToolDescription(
            name="test_tool_lm",
            description="Tool with LM interface",
            args_schema=TestSchema,
            func=test_func,
            risk_level=RiskLevel.LOW,
        )

        result = tool.wrapping_validation()
        assert list(result.args_schema.model_fields.keys()) == ["text"]
        assert result.interface_parameter_names.llm == []
        assert result.interface_parameter_names.embedding == ["embedding"]
        assert result.interface_parameter_names.metrics == []
        assert result.interface_parameter_names.logging == []

    def test_wrapping_validation_with_metrics_interface(self):
        """Test wrapping_validation with MetricsInterface parameter."""

        class TestSchema(BaseModel):
            value: int

        def test_func(value: int, metrics: MetricsInterface) -> int:
            return value

        tool = ToolDescription(
            name="test_tool_metrics",
            description="Tool with Metrics interface",
            args_schema=TestSchema,
            func=test_func,
            risk_level=RiskLevel.LOW,
        )

        result = tool.wrapping_validation()
        assert list(result.args_schema.model_fields.keys()) == ["value"]
        assert result.interface_parameter_names.llm == []
        assert result.interface_parameter_names.embedding == []
        assert result.interface_parameter_names.metrics == ["metrics"]
        assert result.interface_parameter_names.logging == []

    def test_wrapping_validation_with_logging_interface(self):
        """Test wrapping_validation with LoggingInterface parameter."""

        class TestSchema(BaseModel):
            task: str

        def test_func(task: str, logger: LoggingInterface) -> str:
            return f"Processing {task}"

        tool = ToolDescription(
            name="test_tool",
            description="A test tool with logging",
            args_schema=TestSchema,
            func=test_func,
            risk_level=RiskLevel.LOW,
        )

        result = tool.wrapping_validation()

        assert list(result.args_schema.model_fields.keys()) == ["task"]
        assert result.interface_parameter_names.llm == []
        assert result.interface_parameter_names.embedding == []
        assert result.interface_parameter_names.metrics == []
        assert result.interface_parameter_names.logging == ["logger"]

    def test_wrapping_validation_with_all_interfaces(self):
        """Test wrapping_validation with LLM, LM, Metrics, Logging interfaces."""

        class TestSchema(BaseModel):
            query: str

        def test_func(
            query: str,
            llm: LLMInterface,
            embedding: EmbeddingInterface,
            metrics: MetricsInterface,
            logger: LoggingInterface,
        ) -> str:
            return query

        tool = ToolDescription(
            name="test_tool_all_interfaces",
            description="Tool with all interfaces",
            args_schema=TestSchema,
            func=test_func,
            risk_level=RiskLevel.LOW,
        )

        result = tool.wrapping_validation()
        assert list(result.args_schema.model_fields.keys()) == ["query"]
        assert result.interface_parameter_names.llm == ["llm"]
        assert result.interface_parameter_names.embedding == ["embedding"]
        assert result.interface_parameter_names.metrics == ["metrics"]
        assert result.interface_parameter_names.logging == ["logger"]

    def test_wrapping_validation_constants_override_lm_and_metrics(self):
        """Test constants override auto-injection for EmbeddingInterface and MetricsInterface."""

        class TestSchema(BaseModel):
            q: str

        class MockLM(EmbeddingInterface):
            def encode(self, text: str) -> list[float]:  # pragma: no cover
                return [0.2, 0.4, 0.6]

            def encode_batch(self, texts: list[str]) -> list[list[float]]:  # pragma: no cover
                return [[0.2, 0.4, 0.6] for _ in texts]

        class MockMetrics(MetricsInterface):
            def add(self, name: str, value: float) -> None:  # type: ignore[override]
                pass

        def test_func(q: str, embedding: EmbeddingInterface, metrics: MetricsInterface) -> str:
            return q

        tool = ToolDescription(
            name="test_tool_override",
            description="Tool with override",
            args_schema=TestSchema,
            func=test_func,
            risk_level=RiskLevel.LOW,
        )

        # Without constants - auto-inject both
        result = tool.wrapping_validation()
        assert result.interface_parameter_names.llm == []
        assert result.interface_parameter_names.embedding == ["embedding"]
        assert result.interface_parameter_names.metrics == ["metrics"]
        assert result.interface_parameter_names.logging == []

        # With constants overriding both - interfaces are baked into wrapper
        constants = {"embedding": MockLM(), "metrics": MockMetrics()}
        result = tool.wrapping_validation(constants)
        assert result.interface_parameter_names.llm == []
        assert result.interface_parameter_names.embedding == []
        assert result.interface_parameter_names.metrics == []
        assert result.interface_parameter_names.logging == []

    def test_wrapping_validation_missing_parameter(self):
        """Test that wrapping_validation raises error when schema field is missing."""

        class TestSchema(BaseModel):
            name: str
            age: int
            missing_field: str

        def test_func(name: str, age: int) -> str:
            # missing_field is not in function parameters
            return f"{name} is {age}"

        with pytest.raises(
            SignatureValidationError,
            match="Parameter missing_field not found in function signature",
        ):
            ToolDescription(
                name="test_tool",
                description="A test tool",
                args_schema=TestSchema,
                func=test_func,
                risk_level=RiskLevel.LOW,
            )

    def test_wrapping_validation_extra_function_parameters(self):
        """Test wrapping_validation when function has extra parameters not in schema."""

        class TestSchema(BaseModel):
            name: str

        def test_func(name: str, extra_param: int, llm: LLMInterface) -> str:
            return f"{name} with {extra_param}"

        tool = ToolDescription(
            name="test_tool",
            description="A test tool",
            args_schema=TestSchema,
            func=test_func,
            risk_level=RiskLevel.LOW,
        )

        # Should fail because extra_param is required but not provided
        with pytest.raises(ValueError, match="Function parameters.*extra_param.*not provided"):
            tool.wrapping_validation()

        # Should pass when providing the required parameter via constants
        constants = {"extra_param": 42}
        result = tool.wrapping_validation(constants)

        assert list(result.args_schema.model_fields.keys()) == ["name"]
        assert result.interface_parameter_names.llm == ["llm"]
        assert result.interface_parameter_names.embedding == []
        assert result.interface_parameter_names.metrics == []
        assert result.interface_parameter_names.logging == []

    def test_wrapping_validation_no_parameters(self):
        """Test wrapping_validation with function that has no parameters."""

        class EmptySchema(BaseModel):
            pass

        def test_func() -> str:
            return "no parameters"

        tool = ToolDescription(
            name="test_tool",
            description="A test tool",
            args_schema=EmptySchema,
            func=test_func,
            risk_level=RiskLevel.LOW,
        )

        result = tool.wrapping_validation()

        assert list(result.args_schema.model_fields.keys()) == []
        assert result.interface_parameter_names.llm == []
        assert result.interface_parameter_names.embedding == []
        assert result.interface_parameter_names.metrics == []
        assert result.interface_parameter_names.logging == []

    def test_wrapping_validation_complex_types(self):
        """Test wrapping_validation with complex type annotations."""

        class TestSchema(BaseModel):
            items: list[str]
            count: int | None

        def test_func(items: list[str], count: int | None, llm: LLMInterface) -> str:
            return f"{len(items)} items"

        tool = ToolDescription(
            name="test_tool",
            description="A test tool",
            args_schema=TestSchema,
            func=test_func,
            risk_level=RiskLevel.LOW,
        )

        result = tool.wrapping_validation()

        assert set(result.args_schema.model_fields.keys()) == {"items", "count"}
        assert result.interface_parameter_names.llm == ["llm"]
        assert result.interface_parameter_names.embedding == []
        assert result.interface_parameter_names.metrics == []
        assert result.interface_parameter_names.logging == []
        annotations = {k: v.annotation for k, v in result.args_schema.model_fields.items()}
        assert annotations["items"] == list[str]
        assert annotations["count"] == int | None

    def test_from_func_with_valid_docstring(self):
        """Test ToolDescription.from_func with a function that has a valid docstring.

        Requirements:
        - Function name should be used as tool name
        - Function docstring should be used as description (processed by field validator)
        - Function object should be stored as func
        - Provided args_schema should be stored
        """

        class TestSchema(BaseModel):
            message: str
            count: int

        def example_function(message: str, count: int) -> str:
            """
            This is a well-documented function
            that does something useful.

            It has multiple lines with proper indentation.
            """
            return f"{message} * {count}"

        tool = ToolDescription.from_func(example_function, TestSchema, RiskLevel.LOW)

        assert tool.name == "example_function"
        assert (
            tool.description
            == "This is a well-documented function\nthat does something useful.\n\nIt has multiple lines with proper indentation."
        )
        assert tool.func == example_function
        assert tool.args_schema == TestSchema
        assert tool.risk_level == RiskLevel.LOW

    def test_from_func_with_single_line_docstring(self):
        """Test ToolDescription.from_func with a function that has a single-line docstring.

        Requirements:
        - Single-line docstrings should be processed correctly by field validator
        - Leading/trailing whitespace should be stripped
        """

        class TestSchema(BaseModel):
            value: int

        def simple_function(value: int) -> int:
            "A simple function that doubles a value"
            return value * 2

        tool = ToolDescription.from_func(simple_function, TestSchema, RiskLevel.LOW)

        assert tool.name == "simple_function"
        assert tool.description == "A simple function that doubles a value"
        assert tool.func == simple_function
        assert tool.args_schema == TestSchema
        assert tool.risk_level == RiskLevel.LOW

    def test_from_func_with_no_docstring(self):
        """Test ToolDescription.from_func with a function that has no docstring.

        Requirements:
        - Functions without docstrings should raise AssertionError
        - This is because from_func explicitly checks func.__doc__ is not None
        """

        class TestSchema(BaseModel):
            x: float

        def undocumented_function(x: float) -> float:
            return x**2

        with pytest.raises(AssertionError, match="Function must have a docstring for description"):
            ToolDescription.from_func(undocumented_function, TestSchema, RiskLevel.LOW)

    def test_from_func_with_empty_docstring(self):
        """Test ToolDescription.from_func with a function that has an empty docstring.

        Requirements:
        - Empty docstrings should pass from_func (not None) but result in empty description
        - The field validator will process the empty string normally (no assertion)
        """

        class TestSchema(BaseModel):
            data: str

        def empty_doc_function(data: str) -> str:
            """"""
            return data.upper()

        tool = ToolDescription.from_func(empty_doc_function, TestSchema, RiskLevel.LOW)
        assert tool.name == "empty_doc_function"
        assert tool.description == ""  # Empty after dedent().strip()
        assert tool.func == empty_doc_function
        assert tool.args_schema == TestSchema
        assert tool.risk_level == RiskLevel.LOW

    def test_from_func_with_whitespace_only_docstring(self):
        """Test ToolDescription.from_func with a function that has a whitespace-only docstring.

        Requirements:
        - Whitespace-only docstrings should pass from_func (not None) but result in empty description
        - The field validator will strip whitespace, resulting in an empty string
        """

        class TestSchema(BaseModel):
            item: str

        def whitespace_doc_function(item: str) -> str:
            """ """
            return item.lower()

        tool = ToolDescription.from_func(whitespace_doc_function, TestSchema, RiskLevel.LOW)
        assert tool.name == "whitespace_doc_function"
        assert tool.description == ""  # Empty after dedent().strip()
        assert tool.func == whitespace_doc_function
        assert tool.args_schema == TestSchema
        assert tool.risk_level == RiskLevel.LOW

    def test_from_func_strips_docstring_sections(self):
        """Test that from_func strips Args, Returns, Raises sections from docstrings.

        Requirements:
        - Only the description part of the docstring should be kept
        - Args, Returns, Raises, and other sections should be stripped
        - Multi-line descriptions before sections should be preserved
        """

        class TestSchema(BaseModel):
            prompt: str
            max_tokens: int

        def documented_function(prompt: str, max_tokens: int) -> str:
            """Process a prompt and return a response.

            This function handles various input formats.

            Args:
                prompt: The input prompt to process.
                max_tokens: Maximum number of tokens in response.

            Returns:
                The processed response string.

            Raises:
                ValueError: If prompt is empty.
            """
            return f"Response to: {prompt}"

        tool = ToolDescription.from_func(documented_function, TestSchema, RiskLevel.LOW)

        assert tool.name == "documented_function"
        # Only the description part should remain, Args/Returns/Raises stripped
        expected_description = "Process a prompt and return a response.\n\nThis function handles various input formats."
        assert tool.description == expected_description
        assert tool.func == documented_function
        assert tool.args_schema == TestSchema
        assert tool.risk_level == RiskLevel.LOW

    def test_from_func_with_complex_function_signature(self):
        """Test ToolDescription.from_func with functions that have complex signatures.

        Requirements:
        - Should work with functions that have interface parameters
        - Should work with functions that have default values
        - The created ToolDescription should be usable with wrapping_validation
        """

        class TestSchema(BaseModel):
            prompt: str
            max_tokens: int

        def complex_function(prompt: str, max_tokens: int, llm: LLMInterface, multiplier: int = 2) -> str:
            """
            A complex function with multiple parameter types.

            This function demonstrates various parameter patterns.
            """
            return f"Processed: {prompt}"

        tool = ToolDescription.from_func(complex_function, TestSchema, RiskLevel.LOW)

        assert tool.name == "complex_function"
        assert tool.description is not None
        assert "A complex function with multiple parameter types." in tool.description
        assert tool.func == complex_function
        assert tool.args_schema == TestSchema
        assert tool.risk_level == RiskLevel.LOW

        # Test that wrapping_validation works correctly
        result = tool.wrapping_validation()
        assert set(result.args_schema.model_fields.keys()) == {"prompt", "max_tokens"}
        assert result.interface_parameter_names.llm == ["llm"]

    def test_from_func_preserves_function_behavior(self):
        """Test that ToolDescription.from_func preserves the original function's behavior.

        Requirements:
        - The stored function should be callable and work as expected
        - Function identity should be preserved
        """

        class TestSchema(BaseModel):
            a: int
            b: int

        def add_function(a: int, b: int) -> int:
            """Adds two numbers together."""
            return a + b

        tool = ToolDescription.from_func(add_function, TestSchema, RiskLevel.LOW)

        # Test that the function works as expected
        result = tool.func(5, 3)
        assert result == 8

        # Test that it's the same function object
        assert tool.func is add_function
        assert tool.risk_level == RiskLevel.LOW

    def test_from_func_with_async_function(self):
        """Test ToolDescription.from_func with an async function.

        Requirements:
        - Should work with async functions
        - wrapping_validation should correctly detect is_async=True
        """

        class TestSchema(BaseModel):
            data: str

        async def async_function(data: str) -> str:
            """
            An async function for testing.

            This function processes data asynchronously.
            """
            return f"Async: {data}"

        tool = ToolDescription.from_func(async_function, TestSchema, RiskLevel.LOW)

        assert tool.name == "async_function"
        assert tool.description is not None
        assert "An async function for testing." in tool.description
        assert tool.func == async_function
        assert tool.args_schema == TestSchema
        assert tool.risk_level == RiskLevel.LOW

        # Test that wrapping_validation correctly detects async
        result = tool.wrapping_validation()
        import inspect

        assert inspect.iscoroutinefunction(result.func) is True


class TestToolDescriptionConstants:
    """Test cases for ToolDescription constants functionality."""

    def test_wrapping_validation_with_constants_basic(self):
        """Test wrapping_validation with basic constants."""

        class TestSchema(BaseModel):
            name: str

        def test_func(name: str, multiplier: int = 2) -> str:
            return f"{name} * {multiplier}"

        tool = ToolDescription(
            name="test_tool",
            description="A test tool",
            args_schema=TestSchema,
            func=test_func,
            risk_level=RiskLevel.LOW,
        )

        constants = {"multiplier": 5}
        result = tool.wrapping_validation(constants)

        assert list(result.args_schema.model_fields.keys()) == ["name"]
        assert result.interface_parameter_names.llm == []
        assert result.interface_parameter_names.embedding == []
        assert result.interface_parameter_names.metrics == []
        assert result.interface_parameter_names.logging == []

    def test_wrapping_validation_with_constants_providing_required_param(self):
        """Test that constants can provide required parameters."""

        class TestSchema(BaseModel):
            name: str

        def test_func(name: str, required_param: int) -> str:
            return f"{name} with {required_param}"

        tool = ToolDescription(
            name="test_tool",
            description="A test tool",
            args_schema=TestSchema,
            func=test_func,
            risk_level=RiskLevel.LOW,
        )

        # Should fail without constants
        with pytest.raises(ValueError, match="Function parameters.*required_param.*not provided"):
            tool.wrapping_validation()

        # Should pass with constants providing the required parameter
        constants = {"required_param": 42}
        result = tool.wrapping_validation(constants)
        assert list(result.args_schema.model_fields.keys()) == ["name"]
        assert result.interface_parameter_names.llm == []
        assert result.interface_parameter_names.embedding == []
        assert result.interface_parameter_names.metrics == []
        assert result.interface_parameter_names.logging == []

    def test_wrapping_validation_with_interface_constants(self):
        """Test constants can override interface auto-injection."""

        class TestSchema(BaseModel):
            prompt: str

        def test_func(prompt: str, llm: LLMInterface, logger: LoggingInterface) -> str:
            return f"Processing {prompt}"

        class MockLLM(LLMInterface):
            def invoke(self, prompt: str) -> str:
                return f"Mock: {prompt}"

            async def ainvoke(self, prompt: str) -> str:
                return f"Async Mock: {prompt}"

            def invoke_schema(self, prompt: str, schema: type[TSchema]) -> TSchema:
                return schema()  # type: ignore

            async def ainvoke_schema(self, prompt: str, schema: type[TSchema]) -> TSchema:
                return schema()  # type: ignore

        class MockLogger(LoggingInterface):
            def report_progress(self, current: int, total: int, message: str) -> None:
                pass

            async def areport_progress(self, current: int, total: int, message: str) -> None:
                pass

            def log(self, message: str, level: LogLevel | None = None) -> None:
                pass

            async def alog(self, message: str, level: LogLevel | None = None) -> None:
                pass

        tool = ToolDescription(
            name="test_tool",
            description="A test tool with interfaces",
            args_schema=TestSchema,
            func=test_func,
            risk_level=RiskLevel.LOW,
        )

        # Test without constants - should auto-inject both interfaces
        result = tool.wrapping_validation()
        assert result.interface_parameter_names.llm == ["llm"]
        assert result.interface_parameter_names.embedding == []
        assert result.interface_parameter_names.metrics == []
        assert result.interface_parameter_names.logging == ["logger"]

        # Test with constants providing one interface
        constants = {"llm": MockLLM()}
        result = tool.wrapping_validation(constants)
        assert result.interface_parameter_names.llm == []  # No longer needs auto-injection
        assert result.interface_parameter_names.embedding == []
        assert result.interface_parameter_names.metrics == []
        assert result.interface_parameter_names.logging == ["logger"]  # Still needs auto-injection

        # Test with constants providing both interfaces
        constants = {"llm": MockLLM(), "logger": MockLogger()}
        result = tool.wrapping_validation(constants)
        assert result.interface_parameter_names.llm == []
        assert result.interface_parameter_names.embedding == []
        assert result.interface_parameter_names.metrics == []
        assert result.interface_parameter_names.logging == []

    def test_wrapping_validation_missing_required_parameters(self):
        """Test validation fails when required parameters are missing."""

        class TestSchema(BaseModel):
            name: str

        def test_func(name: str, required1: int, required2: str) -> str:
            return f"{name}-{required1}-{required2}"

        tool = ToolDescription(
            name="test_tool",
            description="A test tool",
            args_schema=TestSchema,
            func=test_func,
            risk_level=RiskLevel.LOW,
        )

        # Should fail - missing both required parameters
        with pytest.raises(ValueError, match="Function parameters.*required1.*required2.*not provided"):
            tool.wrapping_validation()

        # Should fail - missing one required parameter
        constants = {"required1": 42}
        with pytest.raises(ValueError, match="Function parameters.*required2.*not provided"):
            tool.wrapping_validation(constants)

        # Should pass - all required parameters provided
        constants = {"required1": 42, "required2": "test"}
        result = tool.wrapping_validation(constants)
        assert list(result.args_schema.model_fields.keys()) == ["name"]

    def test_wrapping_validation_constants_none(self):
        """Test wrapping_validation with constants=None works like no constants."""

        class TestSchema(BaseModel):
            message: str

        def test_func(message: str) -> str:
            return f"Hello {message}"

        tool = ToolDescription(
            name="test_tool",
            description="A test tool",
            args_schema=TestSchema,
            func=test_func,
            risk_level=RiskLevel.LOW,
        )

        result_none = tool.wrapping_validation(None)
        result_empty = tool.wrapping_validation({})
        result_no_param = tool.wrapping_validation()

        # All should be equivalent
        assert (
            list(result_none.args_schema.model_fields.keys())
            == list(result_empty.args_schema.model_fields.keys())
            == list(result_no_param.args_schema.model_fields.keys())
        )
        # Check interface_parameter_names are all empty
        for result in [result_none, result_empty, result_no_param]:
            assert result.interface_parameter_names.llm == []
            assert result.interface_parameter_names.embedding == []
            assert result.interface_parameter_names.metrics == []
            assert result.interface_parameter_names.logging == []

    # === Non-strict type checking for constants ===
    # These tests verify that constants with runtime bare types (e.g., list)
    # are accepted when the annotation is a parameterized type (e.g., list[str])

    def test_wrapping_validation_constants_bare_list_to_parameterized_list(self):
        """Test constants with bare list type matches list[str] annotation.

        This is the primary use case that motivated the non-strict mode:
        type(["ops_board"]) returns list, but the annotation is list[str].
        """

        class TestSchema(BaseModel):
            query: str

        def test_func(query: str, pipelines: list[str]) -> str:
            return f"Processing {query} with {pipelines}"

        tool = ToolDescription(
            name="test_tool",
            description="A test tool with list parameter",
            args_schema=TestSchema,
            func=test_func,
            risk_level=RiskLevel.LOW,
        )

        # Should work - bare list type matches list[str] annotation
        constants = {"pipelines": ["ops_board", "another_pipeline"]}
        result = tool.wrapping_validation(constants)
        assert list(result.args_schema.model_fields.keys()) == ["query"]

    def test_wrapping_validation_constants_bare_list_to_optional_parameterized_list(self):
        """Test constants with bare list type matches list[str] | None annotation.

        This is the exact error case from the original issue:
        type(["ops_board"]) returns list, but the annotation is list[str] | None.
        """

        class TestSchema(BaseModel):
            query: str

        def test_func(query: str, pipelines: list[str] | None = None) -> str:
            return f"Processing {query} with {pipelines}"

        tool = ToolDescription(
            name="test_tool",
            description="A test tool with optional list parameter",
            args_schema=TestSchema,
            func=test_func,
            risk_level=RiskLevel.LOW,
        )

        # Should work - bare list type matches list[str] in the union
        constants = {"pipelines": ["ops_board"]}
        result = tool.wrapping_validation(constants)
        assert list(result.args_schema.model_fields.keys()) == ["query"]

    def test_wrapping_validation_constants_bare_dict_to_parameterized_dict(self):
        """Test constants with bare dict type matches dict[str, Any] annotation."""
        from typing import Any

        class TestSchema(BaseModel):
            name: str

        def test_func(name: str, config: dict[str, Any]) -> str:
            return f"Processing {name} with {config}"

        tool = ToolDescription(
            name="test_tool",
            description="A test tool with dict parameter",
            args_schema=TestSchema,
            func=test_func,
            risk_level=RiskLevel.LOW,
        )

        # Should work - bare dict type matches dict[str, Any] annotation
        constants = {"config": {"key": "value", "count": 42}}
        result = tool.wrapping_validation(constants)
        assert list(result.args_schema.model_fields.keys()) == ["name"]

    def test_wrapping_validation_constants_bare_set_to_parameterized_set(self):
        """Test constants with bare set type matches set[str] annotation."""

        class TestSchema(BaseModel):
            query: str

        def test_func(query: str, tags: set[str]) -> str:
            return f"Processing {query} with tags {tags}"

        tool = ToolDescription(
            name="test_tool",
            description="A test tool with set parameter",
            args_schema=TestSchema,
            func=test_func,
            risk_level=RiskLevel.LOW,
        )

        # Should work - bare set type matches set[str] annotation
        constants = {"tags": {"tag1", "tag2"}}
        result = tool.wrapping_validation(constants)
        assert list(result.args_schema.model_fields.keys()) == ["query"]

    def test_wrapping_validation_constants_incompatible_types_still_fail(self):
        """Test that truly incompatible types still raise ValueError."""

        class TestSchema(BaseModel):
            query: str

        def test_func(query: str, count: int) -> str:
            return f"Processing {query} {count} times"

        tool = ToolDescription(
            name="test_tool",
            description="A test tool",
            args_schema=TestSchema,
            func=test_func,
            risk_level=RiskLevel.LOW,
        )

        # Should fail - string is not compatible with int
        constants = {"count": "not_an_int"}
        with pytest.raises(ValueError, match="Constant for parameter 'count' has type.*str.*not compatible.*int"):
            tool.wrapping_validation(constants)

    def test_wrapping_validation_constants_list_vs_dict_still_fail(self):
        """Test that list constant doesn't match dict annotation."""

        class TestSchema(BaseModel):
            query: str

        def test_func(query: str, config: dict[str, str]) -> str:
            return f"Processing {query}"

        tool = ToolDescription(
            name="test_tool",
            description="A test tool",
            args_schema=TestSchema,
            func=test_func,
            risk_level=RiskLevel.LOW,
        )

        # Should fail - list is not compatible with dict
        constants = {"config": ["item1", "item2"]}
        with pytest.raises(ValueError, match="Constant for parameter 'config' has type.*list.*not compatible.*dict"):
            tool.wrapping_validation(constants)

    def test_wrapping_validation_constants_wrapper_uses_constant_values(self):
        """Test that the wrapped function correctly uses constant values.

        This verifies the wrapper function integrates the constants properly
        and they are not passed at runtime.
        """

        class TestSchema(BaseModel):
            query: str

        def test_func(query: str, pipelines: list[str]) -> str:
            return f"Processing {query} with {','.join(pipelines)}"

        tool = ToolDescription(
            name="test_tool",
            description="A test tool",
            args_schema=TestSchema,
            func=test_func,
            risk_level=RiskLevel.LOW,
        )

        constants = {"pipelines": ["pipeline_a", "pipeline_b"]}
        result = tool.wrapping_validation(constants)

        # Call the wrapper with only schema parameters
        output = result.func(query="test query")
        assert output == "Processing test query with pipeline_a,pipeline_b"

    def test_wrapping_validation_constants_wrapper_rejects_runtime_constant_override(self):
        """Test that the wrapped function rejects attempts to override constants at runtime."""

        class TestSchema(BaseModel):
            query: str

        def test_func(query: str, pipelines: list[str]) -> str:
            return f"Processing {query} with {pipelines}"

        tool = ToolDescription(
            name="test_tool",
            description="A test tool",
            args_schema=TestSchema,
            func=test_func,
            risk_level=RiskLevel.LOW,
        )

        constants = {"pipelines": ["original_pipeline"]}
        result = tool.wrapping_validation(constants)

        # Attempting to pass a constant at runtime should raise an assertion error
        with pytest.raises(AssertionError, match="Runtime violation: constant parameter pipelines provided"):
            result.func(query="test", pipelines=["override_attempt"])


class TestWrappingValidationCustomInterfaces:
    """Test cases for wrapping_validation with custom interface parameters.

    These tests verify that when custom interfaces (custom_llm, custom_embedding,
    custom_metrics, custom_logging) are provided to wrapping_validation:
    1. They are baked into the wrapper function via constants
    2. They do NOT appear in interface_parameter_names since they're pre-bound
    3. The wrapper function correctly receives the custom interfaces when called
    """

    def _create_mock_llm(self) -> LLMInterface:
        """Create a mock LLM interface for testing."""

        class MockLLM(LLMInterface):
            def __init__(self) -> None:
                self.invocations: list[str] = []

            def invoke(self, prompt: str) -> str:
                self.invocations.append(prompt)
                return f"Mock LLM response: {prompt}"

            async def ainvoke(self, prompt: str) -> str:
                self.invocations.append(prompt)
                return f"Async Mock LLM response: {prompt}"

            def invoke_schema(self, prompt: str, schema: type[TSchema]) -> TSchema:
                self.invocations.append(prompt)
                return schema()  # type: ignore

            async def ainvoke_schema(self, prompt: str, schema: type[TSchema]) -> TSchema:
                self.invocations.append(prompt)
                return schema()  # type: ignore

        return MockLLM()

    def _create_mock_embedding(self) -> EmbeddingInterface:
        """Create a mock Embedding interface for testing."""

        class MockEmbedding(EmbeddingInterface):
            def __init__(self) -> None:
                self.encoded_texts: list[str] = []

            def encode(self, text: str) -> list[float]:
                self.encoded_texts.append(text)
                return [0.1, 0.2, 0.3]

            def encode_batch(self, texts: list[str]) -> list[list[float]]:
                self.encoded_texts.extend(texts)
                return [[0.1, 0.2, 0.3] for _ in texts]

        return MockEmbedding()

    def _create_mock_metrics(self) -> MetricsInterface:
        """Create a mock Metrics interface for testing."""

        class MockMetrics(MetricsInterface):
            def __init__(self) -> None:
                self.recorded_metrics: list[tuple[str, float]] = []

            def add(self, name: str, value: float) -> None:  # type: ignore[override]
                self.recorded_metrics.append((name, value))

        return MockMetrics()

    def _create_mock_logging(self) -> LoggingInterface:
        """Create a mock Logging interface for testing."""

        class MockLogging(LoggingInterface):
            def __init__(self) -> None:
                self.log_messages: list[str] = []
                self.progress_reports: list[tuple[int, int, str]] = []

            def report_progress(self, current: int, total: int, message: str) -> None:
                self.progress_reports.append((current, total, message))

            async def areport_progress(self, current: int, total: int, message: str) -> None:
                self.progress_reports.append((current, total, message))

            def log(self, message: str, level: LogLevel | None = None) -> None:
                self.log_messages.append(message)

            async def alog(self, message: str, level: LogLevel | None = None) -> None:
                self.log_messages.append(message)

        return MockLogging()

    def test_custom_llm_is_baked_into_wrapper(self) -> None:
        """Test that when custom_llm is provided, the LLMInterface parameter is baked into wrapper.

        Requirements:
        - When custom_llm is provided, the LLM parameter should NOT appear in interface_parameter_names.llm
        - The custom LLM should be included in the wrapper function's constants
        - Other interface types should still be detected normally
        """

        class TestSchema(BaseModel):
            prompt: str

        def test_func(prompt: str, llm: LLMInterface) -> str:
            return f"Processing: {prompt}"

        tool = ToolDescription(
            name="test_tool",
            description="A test tool with LLM interface",
            args_schema=TestSchema,
            func=test_func,
            risk_level=RiskLevel.LOW,
        )

        custom_llm = self._create_mock_llm()

        # Without custom_llm - should appear in interface_parameter_names
        result_without = tool.wrapping_validation()
        assert result_without.interface_parameter_names.llm == ["llm"]

        # With custom_llm - should NOT appear in interface_parameter_names
        result_with = tool.wrapping_validation(custom_llm=custom_llm)
        assert result_with.interface_parameter_names.llm == []
        assert result_with.interface_parameter_names.embedding == []
        assert result_with.interface_parameter_names.metrics == []
        assert result_with.interface_parameter_names.logging == []

    def test_custom_embedding_is_baked_into_wrapper(self) -> None:
        """Test that when custom_embedding is provided, the EmbeddingInterface parameter is baked into wrapper.

        Requirements:
        - When custom_embedding is provided, the embedding parameter should NOT appear in interface_parameter_names.embedding
        - The custom embedding should be included in the wrapper function's constants
        - Other interface types should still be detected normally
        """

        class TestSchema(BaseModel):
            text: str

        def test_func(text: str, embedding: EmbeddingInterface) -> list[float]:
            return embedding.encode(text)

        tool = ToolDescription(
            name="test_tool",
            description="A test tool with embedding interface",
            args_schema=TestSchema,
            func=test_func,
            risk_level=RiskLevel.LOW,
        )

        custom_embedding = self._create_mock_embedding()

        # Without custom_embedding - should appear in interface_parameter_names
        result_without = tool.wrapping_validation()
        assert result_without.interface_parameter_names.embedding == ["embedding"]

        # With custom_embedding - should NOT appear in interface_parameter_names
        result_with = tool.wrapping_validation(custom_embedding=custom_embedding)
        assert result_with.interface_parameter_names.llm == []
        assert result_with.interface_parameter_names.embedding == []
        assert result_with.interface_parameter_names.metrics == []
        assert result_with.interface_parameter_names.logging == []

    def test_custom_metrics_is_baked_into_wrapper(self) -> None:
        """Test that when custom_metrics is provided, the MetricsInterface parameter is baked into wrapper.

        Requirements:
        - When custom_metrics is provided, the metrics parameter should NOT appear in interface_parameter_names.metrics
        - The custom metrics should be included in the wrapper function's constants
        - Other interface types should still be detected normally
        """

        class TestSchema(BaseModel):
            value: int

        def test_func(value: int, metrics: MetricsInterface) -> int:
            metrics.add("value_processed", float(value))
            return value * 2

        tool = ToolDescription(
            name="test_tool",
            description="A test tool with metrics interface",
            args_schema=TestSchema,
            func=test_func,
            risk_level=RiskLevel.LOW,
        )

        custom_metrics = self._create_mock_metrics()

        # Without custom_metrics - should appear in interface_parameter_names
        result_without = tool.wrapping_validation()
        assert result_without.interface_parameter_names.metrics == ["metrics"]

        # With custom_metrics - should NOT appear in interface_parameter_names
        result_with = tool.wrapping_validation(custom_metrics=custom_metrics)
        assert result_with.interface_parameter_names.llm == []
        assert result_with.interface_parameter_names.embedding == []
        assert result_with.interface_parameter_names.metrics == []
        assert result_with.interface_parameter_names.logging == []

    def test_custom_logging_is_baked_into_wrapper(self) -> None:
        """Test that when custom_logging is provided, the LoggingInterface parameter is baked into wrapper.

        Requirements:
        - When custom_logging is provided, the logging parameter should NOT appear in interface_parameter_names.logging
        - The custom logging should be included in the wrapper function's constants
        - Other interface types should still be detected normally
        """

        class TestSchema(BaseModel):
            task: str

        def test_func(task: str, logger: LoggingInterface) -> str:
            logger.log(f"Starting task: {task}")
            return f"Completed: {task}"

        tool = ToolDescription(
            name="test_tool",
            description="A test tool with logging interface",
            args_schema=TestSchema,
            func=test_func,
            risk_level=RiskLevel.LOW,
        )

        custom_logging = self._create_mock_logging()

        # Without custom_logging - should appear in interface_parameter_names
        result_without = tool.wrapping_validation()
        assert result_without.interface_parameter_names.logging == ["logger"]

        # With custom_logging - should NOT appear in interface_parameter_names
        result_with = tool.wrapping_validation(custom_logging=custom_logging)
        assert result_with.interface_parameter_names.llm == []
        assert result_with.interface_parameter_names.embedding == []
        assert result_with.interface_parameter_names.metrics == []
        assert result_with.interface_parameter_names.logging == []

    def test_combining_multiple_custom_interfaces(self) -> None:
        """Test providing multiple custom interfaces at once.

        Requirements:
        - Multiple custom interfaces can be provided simultaneously
        - All provided custom interfaces should be baked into the wrapper
        - Only the non-custom interface parameters should appear in interface_parameter_names
        - The wrapper function should have access to all custom interfaces
        """

        class TestSchema(BaseModel):
            query: str

        def test_func(
            query: str,
            llm: LLMInterface,
            embedding: EmbeddingInterface,
            metrics: MetricsInterface,
            logger: LoggingInterface,
        ) -> str:
            return f"Processed: {query}"

        tool = ToolDescription(
            name="test_tool",
            description="A test tool with all interfaces",
            args_schema=TestSchema,
            func=test_func,
            risk_level=RiskLevel.LOW,
        )

        custom_llm = self._create_mock_llm()
        custom_embedding = self._create_mock_embedding()
        custom_metrics = self._create_mock_metrics()
        custom_logging = self._create_mock_logging()

        # Without any custom interfaces - all should appear in interface_parameter_names
        result_none = tool.wrapping_validation()
        assert result_none.interface_parameter_names.llm == ["llm"]
        assert result_none.interface_parameter_names.embedding == ["embedding"]
        assert result_none.interface_parameter_names.metrics == ["metrics"]
        assert result_none.interface_parameter_names.logging == ["logger"]

        # With only LLM and embedding custom - metrics and logging should still need injection
        result_partial = tool.wrapping_validation(
            custom_llm=custom_llm,
            custom_embedding=custom_embedding,
        )
        assert result_partial.interface_parameter_names.llm == []
        assert result_partial.interface_parameter_names.embedding == []
        assert result_partial.interface_parameter_names.metrics == ["metrics"]
        assert result_partial.interface_parameter_names.logging == ["logger"]

        # With all custom interfaces - none should need injection
        result_all = tool.wrapping_validation(
            custom_llm=custom_llm,
            custom_embedding=custom_embedding,
            custom_metrics=custom_metrics,
            custom_logging=custom_logging,
        )
        assert result_all.interface_parameter_names.llm == []
        assert result_all.interface_parameter_names.embedding == []
        assert result_all.interface_parameter_names.metrics == []
        assert result_all.interface_parameter_names.logging == []

    def test_wrapper_func_receives_custom_interface(self) -> None:
        """Test that when you call result.func, it actually receives the custom interface.

        Requirements:
        - The wrapper function should correctly receive the custom interface when called
        - The custom interface should be usable within the function
        - The function should only require schema parameters at runtime (not interface params)
        """

        class TestSchema(BaseModel):
            prompt: str

        received_llm: list[LLMInterface] = []

        def test_func(prompt: str, llm: LLMInterface) -> str:
            received_llm.append(llm)
            return llm.invoke(prompt)

        tool = ToolDescription(
            name="test_tool",
            description="A test tool that uses LLM",
            args_schema=TestSchema,
            func=test_func,
            risk_level=RiskLevel.LOW,
        )

        custom_llm = self._create_mock_llm()
        result = tool.wrapping_validation(custom_llm=custom_llm)

        # Call the wrapper function with only schema parameters
        output = result.func(prompt="Hello, world!")

        # Verify the custom LLM was received by the function
        assert len(received_llm) == 1
        assert received_llm[0] is custom_llm

        # Verify the LLM was actually invoked
        assert output == "Mock LLM response: Hello, world!"

    def test_wrapper_func_receives_multiple_custom_interfaces(self) -> None:
        """Test that wrapper receives multiple custom interfaces correctly.

        Requirements:
        - Multiple custom interfaces should all be accessible in the wrapper function
        - Each interface should be the exact instance that was provided
        - The function should work correctly with all interfaces
        """

        class TestSchema(BaseModel):
            data: str

        received_interfaces: dict[str, object] = {}

        def test_func(
            data: str,
            llm: LLMInterface,
            embedding: EmbeddingInterface,
            metrics: MetricsInterface,
            logger: LoggingInterface,
        ) -> str:
            received_interfaces["llm"] = llm
            received_interfaces["embedding"] = embedding
            received_interfaces["metrics"] = metrics
            received_interfaces["logger"] = logger
            logger.log(f"Processing: {data}")
            metrics.add("calls", 1.0)
            return f"Done: {data}"

        tool = ToolDescription(
            name="test_tool",
            description="A test tool with all interfaces",
            args_schema=TestSchema,
            func=test_func,
            risk_level=RiskLevel.LOW,
        )

        custom_llm = self._create_mock_llm()
        custom_embedding = self._create_mock_embedding()
        custom_metrics = self._create_mock_metrics()
        custom_logging = self._create_mock_logging()

        result = tool.wrapping_validation(
            custom_llm=custom_llm,
            custom_embedding=custom_embedding,
            custom_metrics=custom_metrics,
            custom_logging=custom_logging,
        )

        # Call the wrapper function
        output = result.func(data="test data")

        # Verify all custom interfaces were received
        assert received_interfaces["llm"] is custom_llm
        assert received_interfaces["embedding"] is custom_embedding
        assert received_interfaces["metrics"] is custom_metrics
        assert received_interfaces["logger"] is custom_logging

        # Verify the interfaces were used
        assert output == "Done: test data"
        assert custom_logging.log_messages == ["Processing: test data"]  # type: ignore
        assert custom_metrics.recorded_metrics == [("calls", 1.0)]  # type: ignore

    def test_custom_interface_combined_with_constants(self) -> None:
        """Test that custom interfaces work correctly alongside regular constants.

        Requirements:
        - Custom interfaces and regular constants can be provided together
        - Both should be baked into the wrapper function
        - Regular constants should take precedence if there's a name conflict
        """

        class TestSchema(BaseModel):
            name: str

        def test_func(name: str, llm: LLMInterface, multiplier: int) -> str:
            return f"{name} x {multiplier}"

        tool = ToolDescription(
            name="test_tool",
            description="A test tool with LLM and constant",
            args_schema=TestSchema,
            func=test_func,
            risk_level=RiskLevel.LOW,
        )

        custom_llm = self._create_mock_llm()
        constants = {"multiplier": 5}

        result = tool.wrapping_validation(constants=constants, custom_llm=custom_llm)

        # LLM should not appear in interface_parameter_names
        assert result.interface_parameter_names.llm == []

        # Only schema parameters should be in args_schema
        assert list(result.args_schema.model_fields.keys()) == ["name"]

        # Wrapper should work with both baked in
        output = result.func(name="test")
        assert output == "test x 5"

    @pytest.mark.asyncio
    async def test_async_wrapper_receives_custom_interface(self) -> None:
        """Test that async wrapper functions correctly receive custom interfaces.

        Requirements:
        - Async functions should work with custom interfaces
        - The custom interface should be accessible in async context
        - The wrapper should remain async when the original function is async
        """

        class TestSchema(BaseModel):
            prompt: str

        received_llm: list[LLMInterface] = []

        async def test_func(prompt: str, llm: LLMInterface) -> str:
            received_llm.append(llm)
            return await llm.ainvoke(prompt)

        tool = ToolDescription(
            name="test_tool",
            description="An async test tool that uses LLM",
            args_schema=TestSchema,
            func=test_func,
            risk_level=RiskLevel.LOW,
        )

        custom_llm = self._create_mock_llm()
        result = tool.wrapping_validation(custom_llm=custom_llm)

        # Verify the wrapper is async
        import inspect

        assert inspect.iscoroutinefunction(result.func)

        # Call the async wrapper function
        output = await result.func(prompt="Async hello!")

        # Verify the custom LLM was received
        assert len(received_llm) == 1
        assert received_llm[0] is custom_llm

        # Verify the async LLM method was invoked
        assert output == "Async Mock LLM response: Async hello!"
