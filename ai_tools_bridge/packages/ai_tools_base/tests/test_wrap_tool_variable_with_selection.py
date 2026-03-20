"""Tests for wrap_tool_variable_with_selection function.

This module tests the functionality of wrapping tool instance parameters with
selection-based injection, allowing LLMs to select from multiple instances.
"""

from typing import Literal, get_args, get_origin

import pytest
from pydantic import BaseModel, Field

from ai_tools_base import RiskLevel, ToolDescription, wrap_tool_variable_with_selection


class Handler:
    """Base handler class for testing instance parameter injection."""

    def handle(self, a: int, b: int) -> str:
        raise NotImplementedError


class VerboseHandler(Handler):
    """Handler that returns a verbose result."""

    def handle(self, a: int, b: int) -> str:
        result = a + b
        return f"Adding {a} and {b} to get {result}"


class SimpleHandler(Handler):
    """Handler that returns a simple result."""

    def handle(self, a: int, b: int) -> str:
        return str(a + b)


class InputAdd(BaseModel):
    """Schema for the add tool - only LLM-visible parameters."""

    a: int = Field(description="First number")
    b: int = Field(description="Second number")


def add_with_handler(handler: Handler, a: int, b: int) -> str:
    """Add two numbers using the provided handler.

    Args:
        handler: The handler to use for formatting the result.
        a: First number to add.
        b: Second number to add.

    Returns:
        The formatted result from the handler.
    """
    return handler.handle(a, b)


async def async_add_with_handler(handler: Handler, a: int, b: int) -> str:
    """Async version of add_with_handler.

    Args:
        handler: The handler to use for formatting the result.
        a: First number to add.
        b: Second number to add.

    Returns:
        The formatted result from the handler.
    """
    return handler.handle(a, b)


@pytest.fixture
def base_tool() -> ToolDescription:
    """Create a base tool for testing."""
    return ToolDescription(
        name="add_numbers",
        description="Adds two numbers.",
        risk_level=RiskLevel.LOW,
        args_schema=InputAdd,
        func=add_with_handler,
    )


@pytest.fixture
def async_base_tool() -> ToolDescription:
    """Create an async base tool for testing."""
    return ToolDescription(
        name="async_add_numbers",
        description="Adds two numbers asynchronously.",
        risk_level=RiskLevel.LOW,
        args_schema=InputAdd,
        func=async_add_with_handler,
    )


class TestValidation:
    """Tests for input validation of wrap_tool_variable_with_selection."""

    def test_empty_selection_map_raises_error(self, base_tool: ToolDescription) -> None:
        """Providing an empty selection_map should raise ValueError."""
        with pytest.raises(ValueError, match="selection_map cannot be empty"):
            wrap_tool_variable_with_selection(
                tool=base_tool,
                param_name="handler",
                selection_map={},
            )

    def test_param_name_in_schema_raises_error(self) -> None:
        """If param_name exists in the schema, it should raise ValueError.

        Instance parameters should not be LLM-visible in the schema.
        """

        class BadSchema(BaseModel):
            handler: str = Field(description="This should not be here")
            a: int
            b: int

        def bad_func(handler: str, a: int, b: int) -> str:
            return f"{handler}: {a + b}"

        tool = ToolDescription(
            name="bad_tool",
            description="A tool with instance param in schema.",
            risk_level=RiskLevel.LOW,
            args_schema=BadSchema,
            func=bad_func,
        )

        with pytest.raises(
            ValueError,
            match=r"Parameter 'handler' exists in the tool's args_schema.*must not be in the schema",
        ):
            wrap_tool_variable_with_selection(
                tool=tool,
                param_name="handler",
                selection_map={"option1": "value1"},
            )

    def test_param_name_not_in_function_raises_error(self, base_tool: ToolDescription) -> None:
        """If param_name doesn't exist in function signature, should raise ValueError."""
        with pytest.raises(
            ValueError,
            match=r"Parameter 'nonexistent_param' not found in tool function signature.*Available parameters:",
        ):
            wrap_tool_variable_with_selection(
                tool=base_tool,
                param_name="nonexistent_param",
                selection_map={"option1": VerboseHandler()},
            )


class TestSingleOption:
    """Tests for single-option selection maps (constant injection)."""

    def test_single_option_schema_unchanged(self, base_tool: ToolDescription) -> None:
        """With a single option, the schema should remain unchanged."""
        wrapped = wrap_tool_variable_with_selection(
            tool=base_tool,
            param_name="handler",
            selection_map={"only_option": VerboseHandler()},
        )

        # Schema should be the same (no new selection parameter)
        assert set(wrapped.args_schema.model_fields.keys()) == {"a", "b"}

    def test_single_option_injects_instance(self, base_tool: ToolDescription) -> None:
        """With a single option, the instance should be injected as a constant."""
        verbose_handler = VerboseHandler()
        wrapped = wrap_tool_variable_with_selection(
            tool=base_tool,
            param_name="handler",
            selection_map={"verbose": verbose_handler},
        )

        # Call the wrapped function without providing handler
        result = wrapped.func(a=2, b=3)
        assert result == "Adding 2 and 3 to get 5"

    def test_single_option_description_unchanged(self, base_tool: ToolDescription) -> None:
        """With a single option, the description should remain unchanged."""
        wrapped = wrap_tool_variable_with_selection(
            tool=base_tool,
            param_name="handler",
            selection_map={"only_option": VerboseHandler()},
        )

        assert wrapped.description == base_tool.description

    @pytest.mark.asyncio
    async def test_single_option_async_function(self, async_base_tool: ToolDescription) -> None:
        """Single option should work with async functions."""
        verbose_handler = VerboseHandler()
        wrapped = wrap_tool_variable_with_selection(
            tool=async_base_tool,
            param_name="handler",
            selection_map={"verbose": verbose_handler},
        )

        result = await wrapped.func(a=2, b=3)
        assert result == "Adding 2 and 3 to get 5"


class TestMultipleOptions:
    """Tests for multi-option selection maps (Literal parameter)."""

    def test_multi_option_adds_selection_parameter(self, base_tool: ToolDescription) -> None:
        """With multiple options, a selection parameter should be added to schema."""
        wrapped = wrap_tool_variable_with_selection(
            tool=base_tool,
            param_name="handler",
            selection_map={
                "verbose": VerboseHandler(),
                "simple": SimpleHandler(),
            },
        )

        # Schema should have the new selection parameter
        assert "handler_selection" in wrapped.args_schema.model_fields
        assert "a" in wrapped.args_schema.model_fields
        assert "b" in wrapped.args_schema.model_fields

    def test_multi_option_selection_is_literal(self, base_tool: ToolDescription) -> None:
        """The selection parameter should be a Literal type with all options."""
        wrapped = wrap_tool_variable_with_selection(
            tool=base_tool,
            param_name="handler",
            selection_map={
                "verbose": VerboseHandler(),
                "simple": SimpleHandler(),
            },
        )

        selection_field = wrapped.args_schema.model_fields["handler_selection"]
        annotation = selection_field.annotation

        # Check it's a Literal type
        assert get_origin(annotation) is Literal
        # Check it contains the correct options
        assert set(get_args(annotation)) == {"verbose", "simple"}

    def test_multi_option_examples_in_field(self, base_tool: ToolDescription) -> None:
        """The selection parameter should have examples with all options."""
        wrapped = wrap_tool_variable_with_selection(
            tool=base_tool,
            param_name="handler",
            selection_map={
                "verbose": VerboseHandler(),
                "simple": SimpleHandler(),
            },
        )

        selection_field = wrapped.args_schema.model_fields["handler_selection"]
        examples = selection_field.examples

        assert examples is not None
        assert set(examples) == {"verbose", "simple"}

    def test_multi_option_resolves_selection_verbose(self, base_tool: ToolDescription) -> None:
        """Selecting 'verbose' should use VerboseHandler."""
        wrapped = wrap_tool_variable_with_selection(
            tool=base_tool,
            param_name="handler",
            selection_map={
                "verbose": VerboseHandler(),
                "simple": SimpleHandler(),
            },
        )

        result = wrapped.func(a=2, b=3, handler_selection="verbose")
        assert result == "Adding 2 and 3 to get 5"

    def test_multi_option_resolves_selection_simple(self, base_tool: ToolDescription) -> None:
        """Selecting 'simple' should use SimpleHandler."""
        wrapped = wrap_tool_variable_with_selection(
            tool=base_tool,
            param_name="handler",
            selection_map={
                "verbose": VerboseHandler(),
                "simple": SimpleHandler(),
            },
        )

        result = wrapped.func(a=2, b=3, handler_selection="simple")
        assert result == "5"

    def test_multi_option_invalid_selection_raises_error(self, base_tool: ToolDescription) -> None:
        """Providing an invalid selection key should raise ValueError with options."""
        wrapped = wrap_tool_variable_with_selection(
            tool=base_tool,
            param_name="handler",
            selection_map={
                "verbose": VerboseHandler(),
                "simple": SimpleHandler(),
            },
        )

        with pytest.raises(ValueError) as exc_info:
            wrapped.func(a=2, b=3, handler_selection="invalid")

        error_msg = str(exc_info.value)
        assert "Invalid selection 'invalid'" in error_msg
        assert "'verbose'" in error_msg
        assert "'simple'" in error_msg

    def test_multi_option_description_updated(self, base_tool: ToolDescription) -> None:
        """With multiple options, description should include available options."""
        wrapped = wrap_tool_variable_with_selection(
            tool=base_tool,
            param_name="handler",
            selection_map={
                "verbose": VerboseHandler(),
                "simple": SimpleHandler(),
            },
        )

        assert "Available handler_selection options:" in wrapped.description
        assert "'verbose'" in wrapped.description
        assert "'simple'" in wrapped.description

    @pytest.mark.asyncio
    async def test_multi_option_async_function(self, async_base_tool: ToolDescription) -> None:
        """Multiple options should work with async functions."""
        wrapped = wrap_tool_variable_with_selection(
            tool=async_base_tool,
            param_name="handler",
            selection_map={
                "verbose": VerboseHandler(),
                "simple": SimpleHandler(),
            },
        )

        verbose_result = await wrapped.func(a=2, b=3, handler_selection="verbose")
        assert verbose_result == "Adding 2 and 3 to get 5"

        simple_result = await wrapped.func(a=5, b=7, handler_selection="simple")
        assert simple_result == "12"


class TestCustomSelectionParamName:
    """Tests for custom selection parameter name."""

    def test_custom_selection_param_name(self, base_tool: ToolDescription) -> None:
        """Custom selection_param_name should be used in the schema."""
        wrapped = wrap_tool_variable_with_selection(
            tool=base_tool,
            param_name="handler",
            selection_map={
                "verbose": VerboseHandler(),
                "simple": SimpleHandler(),
            },
            selection_param_name="handler_type",
        )

        assert "handler_type" in wrapped.args_schema.model_fields
        assert "handler_selection" not in wrapped.args_schema.model_fields

    def test_custom_selection_param_name_in_description(self, base_tool: ToolDescription) -> None:
        """Custom selection_param_name should appear in the updated description."""
        wrapped = wrap_tool_variable_with_selection(
            tool=base_tool,
            param_name="handler",
            selection_map={
                "verbose": VerboseHandler(),
                "simple": SimpleHandler(),
            },
            selection_param_name="handler_type",
        )

        assert "Available handler_type options:" in wrapped.description

    def test_custom_selection_param_name_works_in_call(self, base_tool: ToolDescription) -> None:
        """The function should accept the custom selection parameter name."""
        wrapped = wrap_tool_variable_with_selection(
            tool=base_tool,
            param_name="handler",
            selection_map={
                "verbose": VerboseHandler(),
                "simple": SimpleHandler(),
            },
            selection_param_name="handler_type",
        )

        result = wrapped.func(a=2, b=3, handler_type="simple")
        assert result == "5"


class TestPreservation:
    """Tests for preservation of tool properties."""

    def test_preserves_name(self, base_tool: ToolDescription) -> None:
        """The wrapped tool should preserve the original name."""
        wrapped = wrap_tool_variable_with_selection(
            tool=base_tool,
            param_name="handler",
            selection_map={"verbose": VerboseHandler()},
        )

        assert wrapped.name == base_tool.name

    def test_preserves_risk_level(self, base_tool: ToolDescription) -> None:
        """The wrapped tool should preserve the original risk level."""
        wrapped = wrap_tool_variable_with_selection(
            tool=base_tool,
            param_name="handler",
            selection_map={"verbose": VerboseHandler()},
        )

        assert wrapped.risk_level == base_tool.risk_level

    def test_original_tool_unchanged(self, base_tool: ToolDescription) -> None:
        """The original tool should not be modified."""
        original_schema_fields = set(base_tool.args_schema.model_fields.keys())
        original_description = base_tool.description

        wrap_tool_variable_with_selection(
            tool=base_tool,
            param_name="handler",
            selection_map={
                "verbose": VerboseHandler(),
                "simple": SimpleHandler(),
            },
        )

        assert set(base_tool.args_schema.model_fields.keys()) == original_schema_fields
        assert base_tool.description == original_description


class TestExtraParameters:
    """Tests for functions with additional parameters not in the LLM schema."""

    def test_single_option_preserves_extra_params_in_signature(self) -> None:
        """With a single option, extra function params should be in wrapper signature."""

        class SchemaWithoutC(BaseModel):
            a: int = Field(description="First number")
            b: int = Field(description="Second number")

        def func_with_extra(handler: Handler, a: int, b: int, c: int) -> str:
            return handler.handle(a, b) + f" with c={c}"

        tool = ToolDescription(
            name="func_with_extra",
            description="Function with extra param c.",
            risk_level=RiskLevel.LOW,
            args_schema=SchemaWithoutC,
            func=func_with_extra,
        )

        wrapped = wrap_tool_variable_with_selection(
            tool=tool,
            param_name="handler",
            selection_map={"verbose": VerboseHandler()},
        )

        # Check that the wrapper function signature includes 'c'
        import inspect

        sig = inspect.signature(wrapped.func)
        assert "c" in sig.parameters
        assert "a" in sig.parameters
        assert "b" in sig.parameters
        # handler should NOT be in signature (it's injected)
        assert "handler" not in sig.parameters

    def test_single_option_extra_param_can_be_called(self) -> None:
        """With a single option, the wrapper should accept extra params."""

        class SchemaWithoutC(BaseModel):
            a: int = Field(description="First number")
            b: int = Field(description="Second number")

        def func_with_extra(handler: Handler, a: int, b: int, c: int) -> str:
            return handler.handle(a, b) + f" with c={c}"

        tool = ToolDescription(
            name="func_with_extra",
            description="Function with extra param c.",
            risk_level=RiskLevel.LOW,
            args_schema=SchemaWithoutC,
            func=func_with_extra,
        )

        wrapped = wrap_tool_variable_with_selection(
            tool=tool,
            param_name="handler",
            selection_map={"verbose": VerboseHandler()},
        )

        result = wrapped.func(a=2, b=3, c=10)
        assert result == "Adding 2 and 3 to get 5 with c=10"

    def test_multi_option_preserves_extra_params_in_signature(self) -> None:
        """With multiple options, extra function params should be in wrapper signature."""

        class SchemaWithoutC(BaseModel):
            a: int = Field(description="First number")
            b: int = Field(description="Second number")

        def func_with_extra(handler: Handler, a: int, b: int, c: int) -> str:
            return handler.handle(a, b) + f" with c={c}"

        tool = ToolDescription(
            name="func_with_extra",
            description="Function with extra param c.",
            risk_level=RiskLevel.LOW,
            args_schema=SchemaWithoutC,
            func=func_with_extra,
        )

        wrapped = wrap_tool_variable_with_selection(
            tool=tool,
            param_name="handler",
            selection_map={
                "verbose": VerboseHandler(),
                "simple": SimpleHandler(),
            },
        )

        # Check that the wrapper function signature includes 'c' and 'handler_selection'
        import inspect

        sig = inspect.signature(wrapped.func)
        assert "c" in sig.parameters
        assert "a" in sig.parameters
        assert "b" in sig.parameters
        assert "handler_selection" in sig.parameters
        # handler should NOT be in signature (it's resolved from selection)
        assert "handler" not in sig.parameters

    def test_multi_option_extra_param_can_be_called(self) -> None:
        """With multiple options, the wrapper should accept extra params."""

        class SchemaWithoutC(BaseModel):
            a: int = Field(description="First number")
            b: int = Field(description="Second number")

        def func_with_extra(handler: Handler, a: int, b: int, c: int) -> str:
            return handler.handle(a, b) + f" with c={c}"

        tool = ToolDescription(
            name="func_with_extra",
            description="Function with extra param c.",
            risk_level=RiskLevel.LOW,
            args_schema=SchemaWithoutC,
            func=func_with_extra,
        )

        wrapped = wrap_tool_variable_with_selection(
            tool=tool,
            param_name="handler",
            selection_map={
                "verbose": VerboseHandler(),
                "simple": SimpleHandler(),
            },
        )

        result = wrapped.func(a=2, b=3, c=10, handler_selection="simple")
        assert result == "5 with c=10"

        result = wrapped.func(a=2, b=3, c=20, handler_selection="verbose")
        assert result == "Adding 2 and 3 to get 5 with c=20"

    def test_extra_param_with_default_preserved(self) -> None:
        """Extra params with defaults should preserve their defaults."""

        class SchemaWithoutC(BaseModel):
            a: int = Field(description="First number")
            b: int = Field(description="Second number")

        def func_with_default_extra(handler: Handler, a: int, b: int, c: int = 100) -> str:
            return handler.handle(a, b) + f" with c={c}"

        tool = ToolDescription(
            name="func_with_default_extra",
            description="Function with extra param c with default.",
            risk_level=RiskLevel.LOW,
            args_schema=SchemaWithoutC,
            func=func_with_default_extra,
        )

        wrapped = wrap_tool_variable_with_selection(
            tool=tool,
            param_name="handler",
            selection_map={"verbose": VerboseHandler()},
        )

        # Check that the default is preserved
        import inspect

        sig = inspect.signature(wrapped.func)
        assert sig.parameters["c"].default == 100

        # Should work without providing c
        result = wrapped.func(a=2, b=3)
        assert result == "Adding 2 and 3 to get 5 with c=100"

        # Should work with custom c
        result = wrapped.func(a=2, b=3, c=50)
        assert result == "Adding 2 and 3 to get 5 with c=50"

    def test_llm_schema_unchanged_with_extra_params(self) -> None:
        """The LLM schema should not include extra params."""

        class SchemaWithoutC(BaseModel):
            a: int = Field(description="First number")
            b: int = Field(description="Second number")

        def func_with_extra(handler: Handler, a: int, b: int, c: int) -> str:
            return handler.handle(a, b) + f" with c={c}"

        tool = ToolDescription(
            name="func_with_extra",
            description="Function with extra param c.",
            risk_level=RiskLevel.LOW,
            args_schema=SchemaWithoutC,
            func=func_with_extra,
        )

        wrapped = wrap_tool_variable_with_selection(
            tool=tool,
            param_name="handler",
            selection_map={"verbose": VerboseHandler()},
        )

        # LLM schema should only have a and b, not c
        assert set(wrapped.args_schema.model_fields.keys()) == {"a", "b"}

    def test_multi_option_llm_schema_unchanged_with_extra_params(self) -> None:
        """The LLM schema should have selection param but not extra params."""

        class SchemaWithoutC(BaseModel):
            a: int = Field(description="First number")
            b: int = Field(description="Second number")

        def func_with_extra(handler: Handler, a: int, b: int, c: int) -> str:
            return handler.handle(a, b) + f" with c={c}"

        tool = ToolDescription(
            name="func_with_extra",
            description="Function with extra param c.",
            risk_level=RiskLevel.LOW,
            args_schema=SchemaWithoutC,
            func=func_with_extra,
        )

        wrapped = wrap_tool_variable_with_selection(
            tool=tool,
            param_name="handler",
            selection_map={
                "verbose": VerboseHandler(),
                "simple": SimpleHandler(),
            },
        )

        # LLM schema should have a, b, and handler_selection, but not c
        assert set(wrapped.args_schema.model_fields.keys()) == {"a", "b", "handler_selection"}

    @pytest.mark.asyncio
    async def test_async_function_with_extra_params(self) -> None:
        """Async functions with extra params should work correctly."""

        class SchemaWithoutC(BaseModel):
            a: int = Field(description="First number")
            b: int = Field(description="Second number")

        async def async_func_with_extra(handler: Handler, a: int, b: int, c: int) -> str:
            return handler.handle(a, b) + f" with c={c}"

        tool = ToolDescription(
            name="async_func_with_extra",
            description="Async function with extra param c.",
            risk_level=RiskLevel.LOW,
            args_schema=SchemaWithoutC,
            func=async_func_with_extra,
        )

        # Test single option
        wrapped_single = wrap_tool_variable_with_selection(
            tool=tool,
            param_name="handler",
            selection_map={"verbose": VerboseHandler()},
        )

        result = await wrapped_single.func(a=2, b=3, c=10)
        assert result == "Adding 2 and 3 to get 5 with c=10"

        # Test multi option
        wrapped_multi = wrap_tool_variable_with_selection(
            tool=tool,
            param_name="handler",
            selection_map={
                "verbose": VerboseHandler(),
                "simple": SimpleHandler(),
            },
        )

        result = await wrapped_multi.func(a=2, b=3, c=10, handler_selection="simple")
        assert result == "5 with c=10"

    def test_multiple_extra_params(self) -> None:
        """Multiple extra params should all be preserved."""

        class SchemaWithoutExtras(BaseModel):
            a: int = Field(description="First number")

        def func_with_multiple_extras(handler: Handler, a: int, b: int, c: int, d: str) -> str:
            return handler.handle(a, b) + f" c={c} d={d}"

        tool = ToolDescription(
            name="func_with_multiple_extras",
            description="Function with multiple extra params.",
            risk_level=RiskLevel.LOW,
            args_schema=SchemaWithoutExtras,
            func=func_with_multiple_extras,
        )

        wrapped = wrap_tool_variable_with_selection(
            tool=tool,
            param_name="handler",
            selection_map={"verbose": VerboseHandler()},
        )

        import inspect

        sig = inspect.signature(wrapped.func)
        assert "a" in sig.parameters
        assert "b" in sig.parameters
        assert "c" in sig.parameters
        assert "d" in sig.parameters

        result = wrapped.func(a=2, b=3, c=10, d="test")
        assert result == "Adding 2 and 3 to get 5 c=10 d=test"

    def test_extra_param_with_arbitrary_type(self) -> None:
        """Extra params with arbitrary types (not Pydantic-compatible) should work.

        This test verifies that extra function parameters with arbitrary class types
        can be preserved in the wrapper signature without going through Pydantic
        model creation, which would fail for non-serializable types.
        """

        class ArbitraryService:
            """A custom service class that Pydantic cannot handle in create_model."""

            def __init__(self, prefix: str) -> None:
                self.prefix = prefix

            def format(self, value: str) -> str:
                return f"{self.prefix}: {value}"

        class SimpleSchema(BaseModel):
            message: str = Field(description="The message to process")

        def func_with_arbitrary_service(
            handler: Handler,
            message: str,
            service: ArbitraryService,
        ) -> str:
            base_result = handler.handle(1, 2)
            return service.format(f"{message} -> {base_result}")

        tool = ToolDescription(
            name="func_with_arbitrary_service",
            description="Function with an arbitrary service type parameter.",
            risk_level=RiskLevel.LOW,
            args_schema=SimpleSchema,
            func=func_with_arbitrary_service,
        )

        # This should NOT raise an error - previously it would fail with:
        # "pydantic.errors.PydanticSchemaGenerationError" when trying to
        # create a model with ArbitraryService as a field type
        wrapped = wrap_tool_variable_with_selection(
            tool=tool,
            param_name="handler",
            selection_map={"verbose": VerboseHandler()},
        )

        # Verify the signature includes the service parameter
        import inspect

        sig = inspect.signature(wrapped.func)
        assert "message" in sig.parameters
        assert "service" in sig.parameters
        assert "handler" not in sig.parameters

        # Verify the LLM schema does NOT include the service parameter
        assert set(wrapped.args_schema.model_fields.keys()) == {"message"}

        # Verify the function can be called with the arbitrary service
        my_service = ArbitraryService(prefix="Result")
        result = wrapped.func(message="hello", service=my_service)
        assert result == "Result: hello -> Adding 1 and 2 to get 3"

    def test_extra_param_with_arbitrary_type_multi_option(self) -> None:
        """Extra params with arbitrary types should work with multiple selection options."""

        class DatabaseConnection:
            """A custom database connection class that Pydantic cannot handle."""

            def __init__(self, name: str) -> None:
                self.name = name

            def query(self, sql: str) -> str:
                return f"[{self.name}] Executed: {sql}"

        class QuerySchema(BaseModel):
            sql: str = Field(description="SQL query to execute")

        def func_with_db_connection(
            handler: Handler,
            sql: str,
            db: DatabaseConnection,
        ) -> str:
            handler_info = handler.handle(0, 0)
            return f"{db.query(sql)} (handler: {handler_info})"

        tool = ToolDescription(
            name="func_with_db_connection",
            description="Function with a database connection parameter.",
            risk_level=RiskLevel.LOW,
            args_schema=QuerySchema,
            func=func_with_db_connection,
        )

        # Multi-option case - should also work without Pydantic errors
        wrapped = wrap_tool_variable_with_selection(
            tool=tool,
            param_name="handler",
            selection_map={
                "verbose": VerboseHandler(),
                "simple": SimpleHandler(),
            },
        )

        # Verify the signature includes db and handler_selection
        import inspect

        sig = inspect.signature(wrapped.func)
        assert "sql" in sig.parameters
        assert "db" in sig.parameters
        assert "handler_selection" in sig.parameters
        assert "handler" not in sig.parameters

        # Verify the LLM schema has sql and handler_selection but NOT db
        assert set(wrapped.args_schema.model_fields.keys()) == {"sql", "handler_selection"}

        # Verify the function works correctly
        my_db = DatabaseConnection(name="TestDB")
        result = wrapped.func(sql="SELECT * FROM users", db=my_db, handler_selection="simple")
        assert result == "[TestDB] Executed: SELECT * FROM users (handler: 0)"
