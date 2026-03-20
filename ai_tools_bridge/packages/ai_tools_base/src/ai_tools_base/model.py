"""Core models and utilities for AI tool descriptions and validation.

This module provides the fundamental data structures for describing and validating
AI tools, including their schemas, functions, and interface requirements.
"""

import inspect
from collections.abc import Callable
from enum import Enum
from inspect import Parameter
from typing import Any, Literal, cast

from pydantic import BaseModel, ConfigDict, Field, create_model, field_validator, model_validator

from .func_signature import (
    apply_schema_to_function,
    extract_description_from_docstring,
    validate_function_signature_to_schema,
)
from .interfaces import (
    EmbeddingInterface,
    LLMInterface,
    LoggingInterface,
    MetricsInterface,
)
from .type_checking import is_type_compatible


class AIToolBaseModel(BaseModel):
    """Base model for AI tool-related Pydantic models.

    This class sets common configuration for all AI tool models, such as allowing
    arbitrary types and forbidding extra fields.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True, extra="forbid")


class InterfaceParameterNames(AIToolBaseModel):
    """Holds the names of parameters in a tool function that correspond to interfaces.

    This class is used to track which parameters in a tool function are intended
    to receive interface implementations, such as LLMs, embeddings, metrics,
    or logging interfaces.
    """

    llm: list[str] = Field(default_factory=list)
    embedding: list[str] = Field(default_factory=list)
    metrics: list[str] = Field(default_factory=list)
    logging: list[str] = Field(default_factory=list)

    @property
    def all(self) -> list[str]:
        """Get a combined list of all interface parameter names."""
        return self.llm + self.embedding + self.metrics + self.logging


class WrappingValidationResult(AIToolBaseModel):
    """Result of validating a tool's function signature and parameter requirements.

    This class contains the analysis results of a tool function's parameters,
    identifying which parameters come from the tool schema, which are interface
    dependencies that can be auto-injected, and validation information needed
    for proper tool execution.
    """

    args_schema: type[BaseModel]
    func: Callable[..., Any]
    interface_parameter_names: InterfaceParameterNames


class PostProcessor(AIToolBaseModel):
    """Defines a post-processing step that can be applied to a tool's output.

    Attributes:
        name: Unique identifier for this post processor.
        func: The function that transforms the tool's output.
        additional_args: Optional Pydantic model defining extra arguments the post
            processor accepts. Reserved for future use to allow post processors
            to receive additional configuration from the tool caller.
    """

    name: str
    func: Callable[..., Any]
    additional_args: type[BaseModel] | None = None


class RiskLevel(Enum):
    """Enumeration of risk levels for AI tools."""

    LOW = "low"  # Only reads data
    MEDIUM = "medium"  # Reads and writes data
    HIGH = "high"  # Deletes or modifies data


class ToolDescription(AIToolBaseModel):
    """Complete description of an AI tool including its function, schema, and metadata.

    This class encapsulates all the information needed to use an AI tool, including
    the function implementation, input schema validation, and descriptive metadata.
    It provides validation and wrapping capabilities to ensure tools can be properly
    integrated into different AI frameworks.
    """

    name: str
    description: str
    risk_level: RiskLevel
    args_schema: type[BaseModel]
    func: Callable[..., Any]
    post_processors: list[PostProcessor] = Field(default_factory=list[PostProcessor])

    @field_validator("description", mode="after")
    @classmethod
    def process_description(cls, v: str) -> str:
        """Clean up description text by removing common leading whitespace.

        Args:
            v: The raw description string.

        Returns:
            The description with consistent indentation removed and whitespace stripped.
        """
        return extract_description_from_docstring(v)

    @model_validator(mode="after")
    def validate_tool(self) -> "ToolDescription":
        validate_function_signature_to_schema(self.func, self.args_schema)
        return self

    @classmethod
    def from_func(
        cls,
        func: Callable[..., Any],
        args_schema: type[BaseModel],
        risk_level: RiskLevel,
        post_processors: list[PostProcessor] | None = None,
    ) -> "ToolDescription":
        """Create a ToolDescription from a function and its argument schema.

        Args:
            func: The function that implements the tool's logic. Must have a docstring.
            args_schema: A Pydantic model class that defines the tool's input schema.

        Returns:
            A ToolDescription instance ready for use in AI frameworks.

        Raises:
            AssertionError: If the function does not have a docstring.
        """
        assert func.__doc__ is not None, "Function must have a docstring for description"

        return ToolDescription(
            name=func.__name__,
            description=extract_description_from_docstring(func.__doc__),
            func=func,
            args_schema=args_schema,
            risk_level=risk_level,
            post_processors=post_processors or [],
        )

    def with_post_processor(self, name: str) -> "ToolDescription":
        """Create a new ToolDescription with the specified post processor applied.

        Args:
            name: The name of the post processor to apply.

        Returns:
            A new ToolDescription instance with the specified post processor.

        Raises:
            ValueError: If the specified post processor is not found.
        """
        post_processors_dict: dict[str, PostProcessor] = {}
        for processor in self.post_processors:
            assert processor.name not in post_processors_dict, f"Duplicate post processor name: {processor.name}"
            post_processors_dict[processor.name] = processor

        if name not in post_processors_dict:
            raise ValueError(f"Post processor '{name}' not found in tool description")

        processor = post_processors_dict[name]

        from .pydantic_utils import combine_base_models

        new_args_schema = self.args_schema

        if processor.additional_args is not None:
            new_args_schema = combine_base_models(
                f"{self.args_schema.__name__}With{processor.additional_args.__name__}",
                self.args_schema,
                processor.additional_args,
            )

        func_signature = inspect.signature(self.func)
        post_signature = inspect.signature(processor.func)

        post_processor_injest_param: Parameter | None = None

        if processor.additional_args is None:
            # Validate that the post processor can accept the additional args
            assert len(post_signature.parameters) == 1, (
                "Post processor with additional_args must accept exactly one parameter for the tool output"
            )
            post_processor_injest_param = list(post_signature.parameters.values())[0]

        else:
            for post_param_name, post_param in post_signature.parameters.items():
                if post_param_name in processor.additional_args.model_fields:
                    continue

                assert post_processor_injest_param is None, (
                    "Post processor function has multiple parameters that do not match "
                    "additional_args fields; cannot determine which is for tool output"
                )
                post_processor_injest_param = post_param

        # Validate that the post processor can accept the output of the tool function
        tool_return_annotation = func_signature.return_annotation
        assert post_processor_injest_param is not None, "Could not determine post processor input parameter"
        post_input_annotation = post_processor_injest_param.annotation

        assert is_type_compatible(tool_return_annotation, post_input_annotation, strict=True), (
            f"Post processor input type {post_input_annotation} is not compatible with "
            f"tool return type {tool_return_annotation}"
        )

        post_input_arg_name = post_processor_injest_param.name

        if inspect.iscoroutinefunction(self.func):

            async def async_wrapper(**kwargs: Any) -> Any:
                post_processor_args: dict[str, Any] = {}
                if processor.additional_args is not None:
                    for arg_name, field_info in processor.additional_args.model_fields.items():  # type: ignore[attr-defined]
                        if arg_name in kwargs:
                            post_processor_args[arg_name] = kwargs.pop(arg_name)
                        elif not field_info.is_required():
                            post_processor_args[arg_name] = field_info.default
                        else:
                            raise ValueError(f"Missing required argument '{arg_name}' for post processor")

                result = await self.func(**kwargs)
                assert post_processor_injest_param is not None, "Could not determine post processor input parameter"
                post_processor_args[post_input_arg_name] = result
                return processor.func(**post_processor_args)

            wrapper = async_wrapper
        else:

            def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
                post_processor_args: dict[str, Any] = {}
                if processor.additional_args is not None:
                    for arg_name, field_info in processor.additional_args.model_fields.items():  # type: ignore[attr-defined]
                        if arg_name in kwargs:
                            post_processor_args[arg_name] = kwargs.pop(arg_name)
                        elif not field_info.is_required():
                            post_processor_args[arg_name] = field_info.default
                        else:
                            raise ValueError(f"Missing required argument '{arg_name}' for post processor")

                result = self.func(**kwargs)
                assert post_processor_injest_param is not None, "Could not determine post processor input parameter"
                post_processor_args[post_input_arg_name] = result
                return processor.func(**post_processor_args)

            wrapper = sync_wrapper

        apply_schema_to_function(wrapper, new_args_schema)

        return ToolDescription(
            name=self.name + f"_{name}",
            description=self.description,
            func=wrapper,
            args_schema=new_args_schema,
            risk_level=self.risk_level,
        )

    def wrapping_validation(
        self,
        constants: dict[str, Any] | None = None,
        custom_llm: LLMInterface | None = None,
        custom_embedding: EmbeddingInterface | None = None,
        custom_metrics: MetricsInterface | None = None,
        custom_logging: LoggingInterface | None = None,
    ) -> WrappingValidationResult:
        """Validate the tool's function signature and parameter requirements.

        This method analyzes the tool function's parameters to determine which ones
        should come from the input schema, which are interface dependencies that can
        be auto-injected, and which are provided as constants. It ensures all required
        parameters can be satisfied when the tool is executed.

        Args:
            constants: Optional dictionary of constant values to provide to the function.
                      These take precedence over auto-injection for matching parameter names.

        Returns:
            A WrappingValidationResult containing the analysis of parameter requirements
            and validation information.

        Raises:
            ValueError: If required parameters cannot be satisfied by the schema,
                       constants, or auto-injection, or if schema parameters don't
                       match function parameters.
        """

        validate_function_signature_to_schema(self.func, self.args_schema)

        assert custom_llm is None or isinstance(custom_llm, LLMInterface)
        assert custom_embedding is None or isinstance(custom_embedding, EmbeddingInterface)
        assert custom_metrics is None or isinstance(custom_metrics, MetricsInterface)
        assert custom_logging is None or isinstance(custom_logging, LoggingInterface)

        # make sure we have a dictionary that we can modify
        if constants is None:
            constants = {}
        else:
            constants = constants.copy()

        tool_arg_schema_names = list(self.args_schema.model_fields)

        func_signature = inspect.signature(self.func)

        interface_parameter_names = InterfaceParameterNames()

        # Collect all function parameters and their types
        for key, value in func_signature.parameters.items():
            if key in constants:
                # check type constant matches parameter annotation
                if not is_type_compatible(type(constants[key]), value.annotation, strict=False):
                    raise ValueError(
                        f"Constant for parameter '{key}' has type {type(constants[key])} "
                        f"which is not compatible with function parameter type {value.annotation}"
                    )
                # Parameter provided by constant - skip further checks
                continue

            if value.annotation == LLMInterface:
                if custom_llm is not None:
                    # Interface provided by custom LLM instance
                    constants[key] = custom_llm
                else:
                    interface_parameter_names.llm.append(key)
            elif value.annotation == EmbeddingInterface:
                if custom_embedding is not None:
                    # Interface provided by custom Embedding instance
                    constants[key] = custom_embedding
                else:
                    interface_parameter_names.embedding.append(key)
            elif value.annotation == MetricsInterface:
                if custom_metrics is not None:
                    # Interface provided by custom Metrics instance
                    constants[key] = custom_metrics
                else:
                    interface_parameter_names.metrics.append(key)
            elif value.annotation == LoggingInterface:
                if custom_logging is not None:
                    # Interface provided by custom Logging instance
                    constants[key] = custom_logging
                else:
                    interface_parameter_names.logging.append(key)

        # remaining constants
        constant_parameters_required: list[str] = []
        for key, value in func_signature.parameters.items():
            if key in constants:
                continue

            if key in tool_arg_schema_names:
                continue

            # Interface parameters are provided at runtime by the framework
            if key in interface_parameter_names.all:
                continue

            if value.default == inspect.Parameter.empty:
                constant_parameters_required.append(key)

        if constant_parameters_required:
            raise ValueError(
                f"Function parameters {constant_parameters_required} not provided by schema "
                f"or constants. Schema provides: {tool_arg_schema_names}, "
                f"constants provide: {list(constants.keys())}"
            )

        # Create new arg schema names excluding those provided by constants
        args_schema: type[BaseModel] = cast(
            type[BaseModel],
            create_model(
                self.args_schema.__name__,
                **{k: (v.annotation, v) for k, v in self.args_schema.model_fields.items() if k not in constants},  # type: ignore[call-overload]
            ),
        )

        if inspect.iscoroutinefunction(self.func):

            async def async_wrapper(**kwargs: Any) -> Any:
                for key in kwargs:
                    assert key not in constants, f"Runtime violation: constant parameter {key} provided at runtime!"
                full_kwargs = {**kwargs, **constants}
                return await self.func(**full_kwargs)

            wrapper = async_wrapper
        else:

            def sync_wrapper(**kwargs: Any) -> Any:
                for key in kwargs:
                    assert key not in constants, f"Runtime violation: constant parameter {key} provided at runtime!"
                full_kwargs = {**kwargs, **constants}
                return self.func(**full_kwargs)

            wrapper = sync_wrapper

        apply_schema_to_function(wrapper, args_schema)

        return WrappingValidationResult(
            args_schema=args_schema,
            func=wrapper,
            interface_parameter_names=interface_parameter_names,
        )


def wrap_tool_variable_with_selection[T](
    tool: ToolDescription,
    param_name: str,
    selection_map: dict[str, T],
    selection_param_name: str | None = None,
) -> ToolDescription:
    """Wrap a tool to replace an instance parameter with a selection parameter.

    This function is useful when you have multiple instances of a service (e.g., multiple
    JIRA instances, GitHub instances) and want the LLM to select which one to use via
    a string key instead of receiving the instance directly.

    For single-option selection maps, the instance is injected as a constant and no
    new parameter is added to the schema. For multi-option selection maps, a new
    Literal[...] parameter is added to the schema for the LLM to select from.

    Args:
        tool: The ToolDescription to wrap.
        param_name: The name of the instance parameter in the tool function that should
            be replaced with selection-based injection.
        selection_map: A dictionary mapping selection keys to instance values. The keys
            become the valid options for the LLM to choose from.
        selection_param_name: Optional name for the selection parameter. Defaults to
            "{param_name}_selection" if not provided.

    Returns:
        A new ToolDescription with either:
        - The same schema but with the instance injected as a constant (single option)
        - An extended schema with a Literal selection parameter (multiple options)

    Raises:
        ValueError: If param_name exists in the tool's args_schema (instance parameters
            must not be in the schema), if selection_map is empty, or if param_name
            doesn't exist in the tool function's signature.
    """
    if selection_param_name is None:
        selection_param_name = f"{param_name}_selection"

    # Validate selection_map is not empty
    if not selection_map:
        raise ValueError("selection_map cannot be empty")

    # Validate param_name is NOT in the schema (instance params should not be LLM-visible)
    if param_name in tool.args_schema.model_fields:
        raise ValueError(
            f"Parameter '{param_name}' exists in the tool's args_schema "
            "but must not be in the schema - they should be injected via constants."
        )

    # Validate param_name exists in the function signature
    func_signature = inspect.signature(tool.func)
    if param_name not in func_signature.parameters:
        raise ValueError(
            f"Parameter '{param_name}' not found in tool function signature. "
            f"Available parameters: {list(func_signature.parameters.keys())}"
        )

    selection_keys = list(selection_map.keys())

    # Identify additional function parameters that are not in the LLM schema
    # and not the param_name being wrapped. These need to be preserved in the
    # wrapper function signature so they can still be provided as constants.
    schema_field_names = set(tool.args_schema.model_fields.keys())
    extra_params: dict[str, tuple[Any, Any]] = {}
    for p_name, p_info in func_signature.parameters.items():
        if p_name == param_name:
            # This is the parameter being wrapped - skip it
            continue
        if p_name in schema_field_names:
            # Already in the LLM schema - skip it
            continue
        # This is an extra parameter that needs to be preserved
        default = p_info.default if p_info.default is not inspect.Parameter.empty else ...
        extra_params[p_name] = (p_info.annotation, default)

    # Single option case: inject as constant, no schema change to LLM schema
    if len(selection_keys) == 1:
        single_key = selection_keys[0]
        single_instance = selection_map[single_key]

        if inspect.iscoroutinefunction(tool.func):

            async def async_single_wrapper(**kwargs: Any) -> Any:
                kwargs[param_name] = single_instance
                return await tool.func(**kwargs)

            wrapper = async_single_wrapper
        else:

            def sync_single_wrapper(**kwargs: Any) -> Any:
                kwargs[param_name] = single_instance
                return tool.func(**kwargs)

            wrapper = sync_single_wrapper

        # Apply schema to wrapper function, including any extra params in the signature
        # Extra params are added directly to the signature without going through
        # Pydantic model creation (which can't handle arbitrary types)
        apply_schema_to_function(wrapper, tool.args_schema, extra_params if extra_params else None)

        return ToolDescription(
            name=tool.name,
            description=tool.description,
            risk_level=tool.risk_level,
            args_schema=tool.args_schema,
            func=wrapper,
            post_processors=tool.post_processors,
        )

    # Multi-option case: add Literal selection parameter to schema
    # Create a Literal type with all selection keys
    selection_literal = Literal[tuple(selection_keys)]  # type: ignore[valid-type]

    # Create new LLM schema extending the original with the selection parameter
    new_schema: type[BaseModel] = cast(
        type[BaseModel],
        create_model(
            f"{tool.args_schema.__name__}WithSelection",
            __base__=tool.args_schema,
            **{
                selection_param_name: (
                    selection_literal,
                    Field(
                        description=f"Select which {param_name} to use.",
                        examples=selection_keys,
                    ),
                )
            },  # type: ignore[call-overload]
        ),
    )

    # Create wrapper that resolves selection to instance
    if inspect.iscoroutinefunction(tool.func):

        async def async_multi_wrapper(**kwargs: Any) -> Any:
            selection_key = kwargs.pop(selection_param_name)
            if selection_key not in selection_map:
                valid_options = ", ".join(f"'{k}'" for k in selection_keys)
                raise ValueError(
                    f"Invalid selection '{selection_key}' for {selection_param_name}. "
                    f"Valid options are: {valid_options}"
                )
            kwargs[param_name] = selection_map[selection_key]
            return await tool.func(**kwargs)

        wrapper = async_multi_wrapper
    else:

        def sync_multi_wrapper(**kwargs: Any) -> Any:
            selection_key = kwargs.pop(selection_param_name)
            if selection_key not in selection_map:
                valid_options = ", ".join(f"'{k}'" for k in selection_keys)
                raise ValueError(
                    f"Invalid selection '{selection_key}' for {selection_param_name}. "
                    f"Valid options are: {valid_options}"
                )
            kwargs[param_name] = selection_map[selection_key]
            return tool.func(**kwargs)

        wrapper = sync_multi_wrapper

    # Apply schema to wrapper function, including any extra params in the signature
    # Extra params are added directly to the signature without going through
    # Pydantic model creation (which can't handle arbitrary types)
    apply_schema_to_function(wrapper, new_schema, extra_params if extra_params else None)

    # Update description with available options
    options_str = ", ".join(f"'{k}'" for k in selection_keys)
    updated_description = f"{tool.description}\n\nAvailable {selection_param_name} options: {options_str}"

    return ToolDescription(
        name=tool.name,
        description=updated_description,
        risk_level=tool.risk_level,
        args_schema=new_schema,
        func=wrapper,
        post_processors=tool.post_processors,
    )
