"""Test cases for func_signature module.

This module tests the validation of function signatures against Pydantic schemas,
including parameter matching, type annotations, default values, and edge cases.
"""

import inspect
from collections.abc import Callable as CallableType
from typing import Any
from unittest import TestCase

from pydantic import BaseModel, Field
from pydantic.fields import FieldInfo

from ai_tools_base.func_signature import (
    SignatureValidationError,
    apply_schema_to_function,
    apply_signature_to_function,
    extract_description_from_docstring,
    field_info_to_parameter,
    schema_to_parameters,
    validate_function_signature_to_schema,
)


# Test schemas
class SimpleSchema(BaseModel):
    """Simple schema with basic types."""

    name: str
    age: int


class SchemaWithDefaults(BaseModel):
    """Schema with default values."""

    name: str
    age: int = 25
    city: str = "Unknown"


class SchemaWithOptional(BaseModel):
    """Schema with optional fields."""

    name: str
    email: str | None = None
    phone: str | None = None


class SchemaWithDefaultFactory(BaseModel):
    """Schema with default_factory."""

    name: str
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, str] = Field(default_factory=dict)


class SchemaWithDescription(BaseModel):
    """Schema with field descriptions."""

    name: str = Field(description="User's name")
    age: int = Field(default=18, description="User's age")


class ComplexSchema(BaseModel):
    """Complex schema with various field types."""

    required_str: str
    optional_int: int | None = None
    default_bool: bool = True
    default_list: list[str] = Field(default_factory=list)
    default_dict: dict[str, int] = Field(default_factory=dict)


# Test functions with matching signatures
def simple_function(name: str, age: int):
    """Function matching SimpleSchema."""
    pass


def function_with_defaults(name: str, age: int = 25, city: str = "Unknown"):
    """Function matching SchemaWithDefaults."""
    pass


def function_with_optional(name: str, email: str | None = None, phone: str | None = None):
    """Function matching SchemaWithOptional."""
    pass


def function_with_default_factory(name: str, tags: list[str] | None = None, metadata: dict[str, str] | None = None):
    """Function with None defaults (will be replaced by factory)."""
    if tags is None:
        tags = []
    if metadata is None:
        metadata = {}


def complex_function(
    required_str: str,
    optional_int: int | None = None,
    default_bool: bool = True,
    default_list: list[str] = [],
    default_dict: dict[str, int] = {},
):
    """Function matching ComplexSchema."""
    pass


# Test functions with mismatching signatures
def function_missing_param(name: str):
    """Function missing a required parameter."""
    pass


def function_wrong_type(name: str, age: str):
    """Function with wrong type annotation."""
    pass


def function_wrong_default(name: str, age: int = 30):
    """Function with wrong default value."""
    pass


def function_extra_param(name: str, age: int, extra: str):
    """Function with extra parameter not in schema."""
    pass


def function_no_annotation(name, age: int):  # type: ignore[no-untyped-def]
    """Function missing type annotation."""
    pass


class TestFieldInfoToParameter(TestCase):
    """Test the field_info_to_parameter function.

    Requirements:
    - Should convert FieldInfo to inspect.Parameter correctly
    - Should handle fields with no defaults
    - Should handle fields with explicit defaults
    - Should handle fields with None as default
    - Should handle fields with default_factory
    - Should preserve type annotations
    """

    def test_field_without_default(self):
        """Field without default should have inspect.Parameter.empty as default."""
        field_info = FieldInfo(annotation=str)
        param = field_info_to_parameter("name", field_info)

        assert param.name == "name"
        assert param.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD
        assert param.default is inspect.Parameter.empty
        assert param.annotation == str

    def test_field_with_default_value(self):
        """Field with explicit default should preserve the default value."""
        field_info = FieldInfo(annotation=int, default=25)
        param = field_info_to_parameter("age", field_info)

        assert param.name == "age"
        assert param.default == 25
        assert param.annotation == int

    def test_field_with_none_default(self):
        """Field with None as default should preserve None."""
        field_info = FieldInfo(annotation=str | None, default=None)  # type: ignore[arg-type]
        param = field_info_to_parameter("email", field_info)

        assert param.name == "email"
        assert param.default is None
        assert param.annotation == str | None

    def test_field_with_default_factory(self):
        """Field with default_factory should call the factory to get default."""
        field_info = FieldInfo(annotation=list[str], default_factory=list)
        param = field_info_to_parameter("tags", field_info)

        assert param.name == "tags"
        assert param.default == []
        assert param.annotation == list[str]

    def test_field_with_dict_default_factory(self):
        """Field with dict default_factory should return empty dict."""
        field_info = FieldInfo(annotation=dict[str, int], default_factory=dict)
        param = field_info_to_parameter("metadata", field_info)

        assert param.name == "metadata"
        assert param.default == {}
        assert param.annotation == dict[str, int]

    def test_parameter_kind(self):
        """All parameters should be POSITIONAL_OR_KEYWORD."""
        field_info = FieldInfo(annotation=str, default="test")
        param = field_info_to_parameter("field", field_info)

        assert param.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD

    def test_custom_default_factory(self):
        """Field with custom default_factory should use factory result."""

        def custom_factory():
            return ["default1", "default2"]

        field_info = FieldInfo(annotation=list[str], default_factory=custom_factory)
        param = field_info_to_parameter("items", field_info)

        assert param.default == ["default1", "default2"]


class TestValidateFunctionSignatureToSchema(TestCase):
    """Test the validate_function_signature_to_schema function.

    Requirements:
    - Should validate matching function signatures successfully
    - Should raise error when parameter is missing
    - Should raise error when annotation mismatches
    - Should raise error when default value mismatches
    - Should handle optional parameters correctly
    - Should handle default_factory fields
    - Should handle complex schemas with multiple field types
    """

    def test_simple_matching_signature(self):
        """Function with matching simple signature should validate successfully."""
        # Should not raise any exception
        validate_function_signature_to_schema(simple_function, SimpleSchema)

    def test_signature_with_defaults(self):
        """Function with matching defaults should validate successfully."""
        validate_function_signature_to_schema(function_with_defaults, SchemaWithDefaults)

    def test_signature_with_optional(self):
        """Function with optional parameters should validate successfully."""
        validate_function_signature_to_schema(function_with_optional, SchemaWithOptional)

    def test_complex_signature(self):
        """Function with complex signature should validate successfully."""
        validate_function_signature_to_schema(complex_function, ComplexSchema)

    def test_missing_parameter_raises_error(self):
        """Function missing a required parameter should raise SignatureValidationError."""
        with self.assertRaises(SignatureValidationError) as context:
            validate_function_signature_to_schema(function_missing_param, SimpleSchema)

        assert "age" in str(context.exception)
        assert "not found in function signature" in str(context.exception)

    def test_wrong_annotation_raises_error(self):
        """Function with wrong type annotation should raise SignatureValidationError."""
        with self.assertRaises(SignatureValidationError) as context:
            validate_function_signature_to_schema(function_wrong_type, SimpleSchema)

        assert "Annotation mismatch" in str(context.exception)
        assert "age" in str(context.exception)

    def test_wrong_default_raises_error(self):
        """Function with wrong default value should raise SignatureValidationError."""
        with self.assertRaises(SignatureValidationError) as context:
            validate_function_signature_to_schema(function_wrong_default, SchemaWithDefaults)

        assert "Default value mismatch" in str(context.exception)
        assert "age" in str(context.exception)

    def test_missing_annotation_raises_error(self):
        """Function missing type annotation should raise SignatureValidationError."""
        with self.assertRaises(SignatureValidationError) as context:
            validate_function_signature_to_schema(function_no_annotation, SimpleSchema)  # type: ignore[arg-type]

        assert "Annotation mismatch" in str(context.exception)

    def test_extra_parameter_is_allowed(self):
        """Function with extra parameters should still validate (only schema params checked)."""
        # The validation only checks that schema fields exist in function,
        # it doesn't check for extra parameters in the function
        validate_function_signature_to_schema(function_extra_param, SimpleSchema)

    def test_schema_with_description_validates(self):
        """Schema with field descriptions should validate correctly."""

        def func_with_desc(name: str, age: int = 18):
            pass

        validate_function_signature_to_schema(func_with_desc, SchemaWithDescription)

    def test_default_factory_validation(self):
        """Function should validate against schema with default_factory fields."""
        # The optional mutable pattern (Optional[MutableType] = None) is now allowed
        # because it's a Python best practice to avoid mutable default arguments

        def func_with_factory(name: str, tags: list[str] | None = None, metadata: dict[str, str] | None = None):  # noqa: ARG001
            if tags is None:
                tags = []
            if metadata is None:
                metadata = {}

        # This should now pass - the Optional[list] = None pattern is allowed for mutable defaults
        validate_function_signature_to_schema(func_with_factory, SchemaWithDefaultFactory)  # type: ignore[arg-type]

    def test_default_factory_matching_signature(self):
        """Function with factory-equivalent defaults should match when using same default."""

        def func_with_list_default(name: str, tags: list[str] = [], metadata: dict[str, str] = {}):
            pass

        # This should work because [] == [] and {} == {}
        validate_function_signature_to_schema(func_with_list_default, SchemaWithDefaultFactory)

    def test_bool_default_validation(self):
        """Function with bool default should validate correctly."""

        def func_with_bool(value: bool = True):
            pass

        class BoolSchema(BaseModel):
            value: bool = True

        validate_function_signature_to_schema(func_with_bool, BoolSchema)

    def test_false_bool_default(self):
        """Function with False default should validate correctly."""

        def func_with_false(value: bool = False):
            pass

        class FalseBoolSchema(BaseModel):
            value: bool = False

        validate_function_signature_to_schema(func_with_false, FalseBoolSchema)

    def test_bool_default_mismatch(self):
        """Function with wrong bool default should raise error."""

        def func_with_wrong_bool(value: bool = False):
            pass

        class TrueBoolSchema(BaseModel):
            value: bool = True

        with self.assertRaises(SignatureValidationError) as context:
            validate_function_signature_to_schema(func_with_wrong_bool, TrueBoolSchema)

        assert "Default value mismatch" in str(context.exception)

    def test_empty_schema(self):
        """Function should validate against empty schema."""

        def empty_func():
            pass

        class EmptySchema(BaseModel):
            pass

        validate_function_signature_to_schema(empty_func, EmptySchema)

    def test_single_field_schema(self):
        """Function should validate against single-field schema."""

        def single_param_func(value: str):
            pass

        class SingleFieldSchema(BaseModel):
            value: str

        validate_function_signature_to_schema(single_param_func, SingleFieldSchema)

    def test_numeric_defaults(self):
        """Function with various numeric defaults should validate correctly."""

        def func_with_numbers(int_val: int = 42, float_val: float = 3.14, zero_val: int = 0):
            pass

        class NumericSchema(BaseModel):
            int_val: int = 42
            float_val: float = 3.14
            zero_val: int = 0

        validate_function_signature_to_schema(func_with_numbers, NumericSchema)

    def test_string_defaults(self):
        """Function with string defaults should validate correctly."""

        def func_with_strings(name: str = "John", empty: str = "", city: str = "New York"):
            pass

        class StringSchema(BaseModel):
            name: str = "John"
            empty: str = ""
            city: str = "New York"

        validate_function_signature_to_schema(func_with_strings, StringSchema)

    def test_nested_type_annotations(self):
        """Function with nested type annotations should validate correctly."""

        def func_with_nested(items: list[dict[str, int]]):
            pass

        class NestedSchema(BaseModel):
            items: list[dict[str, int]]

        validate_function_signature_to_schema(func_with_nested, NestedSchema)

    def test_union_type_annotations(self):
        """Function with Union type annotations should validate correctly."""

        def func_with_union(value: str | int):
            pass

        class UnionSchema(BaseModel):
            value: str | int

        validate_function_signature_to_schema(func_with_union, UnionSchema)

    def test_callable_annotation(self):
        """Function with callable annotation should validate correctly."""

        def func_with_callable(callback: CallableType[[str], int]):
            pass

        class CallableSchema(BaseModel):
            callback: CallableType[[str], int]

        validate_function_signature_to_schema(func_with_callable, CallableSchema)


class TestEdgeCases(TestCase):
    """Test edge cases and special scenarios.

    Requirements:
    - Should handle None values correctly
    - Should distinguish between None and empty
    - Should handle mutable default values
    - Should handle special Pydantic field configurations
    """

    def test_none_vs_undefined(self):
        """Should distinguish between None default and no default."""

        def func_with_none(value: str | None = None):
            pass

        def func_without_default(value: str | None):
            pass

        class NoneSchema(BaseModel):
            value: str | None = None

        class NoDefaultSchema(BaseModel):
            value: str | None

        # This should work
        validate_function_signature_to_schema(func_with_none, NoneSchema)

        # This should fail - function has default but schema doesn't
        with self.assertRaises(SignatureValidationError):
            validate_function_signature_to_schema(func_with_none, NoDefaultSchema)

        # This should fail - function has no default but schema does
        with self.assertRaises(SignatureValidationError):
            validate_function_signature_to_schema(func_without_default, NoneSchema)

    def test_empty_list_vs_none(self):
        """Should distinguish between empty list and None."""

        def func_with_empty_list(items: list[str] = []):
            pass

        def func_with_none_list(items: list[str] | None = None):
            pass

        class EmptyListSchema(BaseModel):
            items: list[str] = Field(default_factory=list)

        class NoneListSchema(BaseModel):
            items: list[str] | None = None

        # Empty list should match default_factory
        validate_function_signature_to_schema(func_with_empty_list, EmptyListSchema)

        # None should match None
        validate_function_signature_to_schema(func_with_none_list, NoneListSchema)

        # Cross validation: Optional[list] = None should also match list with default_factory
        # This is valid because using None default for mutable types is a Python best practice
        validate_function_signature_to_schema(func_with_none_list, EmptyListSchema)

    def test_optional_container_pattern_annotation_mismatch(self):
        """Should raise error when optional container pattern has wrong annotation type.

        When the function has a None default and schema expects a container type,
        the function annotation must be Optional[ContainerType], not some other type.
        """

        def func_with_wrong_annotation(items: str | None = None):
            pass

        class ListSchema(BaseModel):
            items: list[str] = Field(default_factory=list)

        # Should fail because str | None doesn't match list[str] | None
        with self.assertRaises(SignatureValidationError) as context:
            validate_function_signature_to_schema(func_with_wrong_annotation, ListSchema)

        assert "Annotation mismatch for optional mutable parameter" in str(context.exception)

    def test_optional_set_pattern(self):
        """Should allow Optional[set] = None pattern for set schema fields."""

        def func_with_set(items: set[str] | None = None):
            if items is None:
                items = set()

        class SetSchema(BaseModel):
            items: set[str] = Field(default_factory=set)

        validate_function_signature_to_schema(func_with_set, SetSchema)

    def test_multiple_validation_errors(self):
        """Should report first error encountered."""

        def bad_func(name: int, age: str = "wrong"):
            pass

        # Will fail on first mismatch found
        with self.assertRaises(SignatureValidationError):
            validate_function_signature_to_schema(bad_func, SimpleSchema)

    def test_parameter_order_irrelevant(self):
        """Parameter order in function doesn't matter for validation."""

        def reordered_func(age: int, name: str):
            pass

        # Should still validate successfully
        validate_function_signature_to_schema(reordered_func, SimpleSchema)

    def test_lambda_function(self):
        """Lambda functions should validate like regular functions."""
        lambda_func: CallableType[[str, int], None] = lambda name, age: None  # noqa: E731
        lambda_func.__annotations__ = {"name": str, "age": int}

        validate_function_signature_to_schema(lambda_func, SimpleSchema)  # type: ignore[arg-type]

    def test_field_info_with_alias(self):
        """Field with alias should use field name, not alias."""

        class AliasSchema(BaseModel):
            user_name: str = Field(alias="userName")

        def func_with_field_name(user_name: str):
            pass

        # Validation uses field name, not alias
        validate_function_signature_to_schema(func_with_field_name, AliasSchema)


class TestSchemaToParameters(TestCase):
    """Test the schema_to_parameters function.

    Requirements:
    - Should convert an empty schema to an empty list
    - Should convert a single field schema to a single parameter
    - Should convert multiple fields to multiple parameters
    - Should handle fields with defaults vs no defaults
    - Should handle fields with default_factory
    - Should preserve field order
    """

    def test_empty_schema(self):
        """Empty schema should return empty list of parameters."""

        class EmptySchema(BaseModel):
            pass

        params = schema_to_parameters(EmptySchema)

        assert params == []

    def test_single_field_schema(self):
        """Single field schema should return list with one parameter."""

        class SingleFieldSchema(BaseModel):
            name: str

        params = schema_to_parameters(SingleFieldSchema)

        assert len(params) == 1
        assert params[0].name == "name"
        assert params[0].annotation == str
        assert params[0].default is inspect.Parameter.empty
        assert params[0].kind == inspect.Parameter.POSITIONAL_OR_KEYWORD

    def test_multiple_fields(self):
        """Multiple fields should return multiple parameters in order."""

        class MultiFieldSchema(BaseModel):
            first: str
            second: int
            third: bool

        params = schema_to_parameters(MultiFieldSchema)

        assert len(params) == 3
        assert params[0].name == "first"
        assert params[0].annotation == str
        assert params[1].name == "second"
        assert params[1].annotation == int
        assert params[2].name == "third"
        assert params[2].annotation == bool

    def test_fields_with_defaults(self):
        """Fields with defaults should have default values in parameters."""

        class DefaultsSchema(BaseModel):
            required: str
            with_default: int = 42
            with_none: str | None = None

        params = schema_to_parameters(DefaultsSchema)

        assert len(params) == 3
        # Required field has no default
        assert params[0].name == "required"
        assert params[0].default is inspect.Parameter.empty
        # Field with default value
        assert params[1].name == "with_default"
        assert params[1].default == 42
        # Field with None default
        assert params[2].name == "with_none"
        assert params[2].default is None

    def test_fields_with_default_factory(self):
        """Fields with default_factory should call factory to get default."""

        class FactorySchema(BaseModel):
            tags: list[str] = Field(default_factory=list)
            data: dict[str, int] = Field(default_factory=dict)

        params = schema_to_parameters(FactorySchema)

        assert len(params) == 2
        assert params[0].name == "tags"
        assert params[0].default == []
        assert params[0].annotation == list[str]
        assert params[1].name == "data"
        assert params[1].default == {}
        assert params[1].annotation == dict[str, int]

    def test_mixed_defaults_and_required(self):
        """Schema with mix of required and optional fields should be converted correctly."""

        class MixedSchema(BaseModel):
            name: str
            age: int = 25
            email: str | None = None
            tags: list[str] = Field(default_factory=list)

        params = schema_to_parameters(MixedSchema)

        assert len(params) == 4
        assert params[0].default is inspect.Parameter.empty  # name - required
        assert params[1].default == 25  # age - default value
        assert params[2].default is None  # email - None default
        assert params[3].default == []  # tags - default_factory

    def test_custom_default_factory(self):
        """Custom default_factory should be called to get default value."""

        def custom_factory() -> list[str]:
            return ["a", "b", "c"]

        class CustomFactorySchema(BaseModel):
            items: list[str] = Field(default_factory=custom_factory)

        params = schema_to_parameters(CustomFactorySchema)

        assert len(params) == 1
        assert params[0].default == ["a", "b", "c"]

    def test_parameters_sorted_required_before_optional(self):
        """Parameters should be sorted so required params come before optional ones.

        This ensures the generated signature is valid Python - parameters with defaults
        cannot precede parameters without defaults.
        """

        class UnorderedSchema(BaseModel):
            optional_first: str = "default"
            required_middle: int
            optional_second: bool = True
            required_last: float

        params = schema_to_parameters(UnorderedSchema)

        assert len(params) == 4
        # Required parameters should come first
        assert params[0].default is inspect.Parameter.empty
        assert params[1].default is inspect.Parameter.empty
        # Optional parameters should come after
        assert params[2].default is not inspect.Parameter.empty
        assert params[3].default is not inspect.Parameter.empty
        # Check the actual names
        required_names = {params[0].name, params[1].name}
        optional_names = {params[2].name, params[3].name}
        assert required_names == {"required_middle", "required_last"}
        assert optional_names == {"optional_first", "optional_second"}

    def test_sorted_parameters_create_valid_signature(self):
        """Converting sorted parameters to a Signature should not raise an error.

        Python raises ValueError if parameters with defaults precede those without.
        """

        class ProblematicOrderSchema(BaseModel):
            with_default: str = "value"
            without_default: int

        params = schema_to_parameters(ProblematicOrderSchema)

        # This would raise ValueError if params weren't sorted correctly:
        # "non-default argument follows default argument"
        signature = inspect.Signature(parameters=params)

        # Verify the signature is valid and has correct parameter order
        param_names = list(signature.parameters.keys())
        assert param_names[0] == "without_default"
        assert param_names[1] == "with_default"


class TestApplySchemaToFunction(TestCase):
    """Test the apply_schema_to_function function.

    Requirements:
    - Should update __annotations__ with schema field annotations
    - Should update __signature__ with schema parameters
    - Should preserve return annotation from original function
    - Should work with async functions
    - Should handle empty schemas
    """

    def test_annotations_updated(self):
        """Function __annotations__ should be updated with schema field types."""

        def target_func(**kwargs: Any) -> None:
            pass

        class AnnotationSchema(BaseModel):
            name: str
            age: int

        apply_schema_to_function(target_func, AnnotationSchema)

        assert "name" in target_func.__annotations__
        assert "age" in target_func.__annotations__
        assert target_func.__annotations__["name"] == str
        assert target_func.__annotations__["age"] == int

    def test_signature_updated(self):
        """Function __signature__ should be updated with schema parameters."""

        def target_func(**kwargs: Any) -> None:
            pass

        class SignatureSchema(BaseModel):
            name: str
            count: int = 10

        apply_schema_to_function(target_func, SignatureSchema)

        sig = inspect.signature(target_func)
        params = list(sig.parameters.values())

        assert len(params) == 2
        assert params[0].name == "name"
        assert params[0].annotation == str
        assert params[0].default is inspect.Parameter.empty
        assert params[1].name == "count"
        assert params[1].annotation == int
        assert params[1].default == 10

    def test_return_annotation_preserved(self):
        """Return annotation from original function should be preserved."""

        def target_func(**kwargs: Any) -> str:
            return ""

        class TestSchema(BaseModel):
            value: int

        apply_schema_to_function(target_func, TestSchema)

        sig = inspect.signature(target_func)
        assert sig.return_annotation == str
        assert target_func.__annotations__.get("return") == str

    def test_async_function(self):
        """Async functions should have their signature updated correctly."""

        async def async_target(**kwargs: Any) -> dict[str, int]:
            return {}

        class AsyncSchema(BaseModel):
            query: str
            limit: int = 100

        apply_schema_to_function(async_target, AsyncSchema)

        sig = inspect.signature(async_target)
        params = list(sig.parameters.values())

        assert len(params) == 2
        assert params[0].name == "query"
        assert params[1].name == "limit"
        assert params[1].default == 100
        assert sig.return_annotation == dict[str, int]

    def test_empty_schema(self):
        """Empty schema should result in function with no parameters."""

        def target_func(**kwargs: Any) -> None:
            pass

        class EmptySchema(BaseModel):
            pass

        apply_schema_to_function(target_func, EmptySchema)

        sig = inspect.signature(target_func)
        assert len(sig.parameters) == 0

    def test_replaces_existing_signature(self):
        """Existing function signature should be completely replaced."""

        def target_func(old_param: float, another: bool = True) -> None:
            pass

        class NewSchema(BaseModel):
            new_param: str
            other: int

        apply_schema_to_function(target_func, NewSchema)

        sig = inspect.signature(target_func)
        param_names = list(sig.parameters.keys())

        assert "old_param" not in param_names
        assert "another" not in param_names
        assert "new_param" in param_names
        assert "other" in param_names

    def test_complex_annotations_preserved(self):
        """Complex type annotations should be correctly applied."""

        def target_func(**kwargs: Any) -> None:
            pass

        class ComplexAnnotationSchema(BaseModel):
            items: list[dict[str, int]]
            callback: CallableType[[str], bool] | None = None

        apply_schema_to_function(target_func, ComplexAnnotationSchema)

        assert target_func.__annotations__["items"] == list[dict[str, int]]
        assert target_func.__annotations__["callback"] == CallableType[[str], bool] | None


class TestApplySignatureToFunction(TestCase):
    """Test the apply_signature_to_function function.

    Requirements:
    - Should set __signature__ attribute correctly
    - Should update __annotations__ from signature parameters
    - Should preserve return annotation if it exists in original function
    - Should handle signatures with various parameter kinds
    """

    def test_signature_set_correctly(self):
        """Function __signature__ should be set to the provided signature."""

        def target_func():  # type: ignore[no-untyped-def]
            pass

        new_sig = inspect.Signature(
            parameters=[
                inspect.Parameter("x", inspect.Parameter.POSITIONAL_OR_KEYWORD, annotation=int),
                inspect.Parameter("y", inspect.Parameter.POSITIONAL_OR_KEYWORD, annotation=str, default="default"),
            ]
        )

        apply_signature_to_function(target_func, new_sig)

        sig = inspect.signature(target_func)
        params = list(sig.parameters.values())

        assert len(params) == 2
        assert params[0].name == "x"
        assert params[0].annotation == int
        assert params[0].default is inspect.Parameter.empty
        assert params[1].name == "y"
        assert params[1].annotation == str
        assert params[1].default == "default"

    def test_annotations_updated(self):
        """Function __annotations__ should be updated from signature parameters."""

        def target_func():  # type: ignore[no-untyped-def]
            pass

        new_sig = inspect.Signature(
            parameters=[
                inspect.Parameter("name", inspect.Parameter.POSITIONAL_OR_KEYWORD, annotation=str),
                inspect.Parameter("value", inspect.Parameter.POSITIONAL_OR_KEYWORD, annotation=float),
            ]
        )

        apply_signature_to_function(target_func, new_sig)

        assert target_func.__annotations__["name"] == str
        assert target_func.__annotations__["value"] == float

    def test_return_annotation_preserved(self):
        """Return annotation from original function should be preserved in __annotations__."""

        def target_func() -> list[str]:
            return []

        new_sig = inspect.Signature(
            parameters=[
                inspect.Parameter("items", inspect.Parameter.POSITIONAL_OR_KEYWORD, annotation=int),
            ]
        )

        apply_signature_to_function(target_func, new_sig)

        assert target_func.__annotations__["return"] == list[str]
        assert target_func.__annotations__["items"] == int

    def test_return_annotation_not_added_if_missing(self):
        """If original function has no return annotation, it should not be added."""

        def target_func():  # type: ignore[no-untyped-def]
            pass

        new_sig = inspect.Signature(
            parameters=[
                inspect.Parameter("x", inspect.Parameter.POSITIONAL_OR_KEYWORD, annotation=int),
            ]
        )

        apply_signature_to_function(target_func, new_sig)

        assert "return" not in target_func.__annotations__
        assert target_func.__annotations__["x"] == int

    def test_empty_signature(self):
        """Empty signature should result in empty parameters and annotations."""

        def target_func(old: str) -> None:
            pass

        new_sig = inspect.Signature(parameters=[])

        apply_signature_to_function(target_func, new_sig)

        sig = inspect.signature(target_func)
        assert len(sig.parameters) == 0
        # Only return annotation should remain (None value, not NoneType class)
        assert target_func.__annotations__ == {"return": None}

    def test_signature_with_return_annotation(self):
        """Signature with return annotation should be applied correctly."""

        def target_func():  # type: ignore[no-untyped-def]
            pass

        new_sig = inspect.Signature(
            parameters=[
                inspect.Parameter("x", inspect.Parameter.POSITIONAL_OR_KEYWORD, annotation=int),
            ],
            return_annotation=bool,
        )

        apply_signature_to_function(target_func, new_sig)

        sig = inspect.signature(target_func)
        assert sig.return_annotation == bool

    def test_replaces_existing_annotations(self):
        """Existing annotations should be replaced, not merged."""

        def target_func(old_param: str, another: int) -> None:
            pass

        new_sig = inspect.Signature(
            parameters=[
                inspect.Parameter("new_param", inspect.Parameter.POSITIONAL_OR_KEYWORD, annotation=float),
            ]
        )

        apply_signature_to_function(target_func, new_sig)

        assert "old_param" not in target_func.__annotations__
        assert "another" not in target_func.__annotations__
        assert target_func.__annotations__["new_param"] == float
        # Python stores -> None as None value, not NoneType class
        assert target_func.__annotations__["return"] is None

    def test_with_default_factory_values(self):
        """Parameters with default values from factory should be handled correctly."""

        def target_func():  # type: ignore[no-untyped-def]
            pass

        new_sig = inspect.Signature(
            parameters=[
                inspect.Parameter("items", inspect.Parameter.POSITIONAL_OR_KEYWORD, annotation=list[str], default=[]),
                inspect.Parameter(
                    "mapping", inspect.Parameter.POSITIONAL_OR_KEYWORD, annotation=dict[str, int], default={}
                ),
            ]
        )

        apply_signature_to_function(target_func, new_sig)

        sig = inspect.signature(target_func)
        params = list(sig.parameters.values())

        assert params[0].default == []
        assert params[1].default == {}


class TestExtractDescriptionFromDocstring(TestCase):
    """Test the extract_description_from_docstring function."""

    def test_empty_docstring(self):
        """Test that an empty docstring returns an empty string."""
        result = extract_description_from_docstring("")
        self.assertEqual(result, "")

    def test_none_docstring(self):
        """Test that None docstring returns an empty string."""
        result = extract_description_from_docstring(None)
        self.assertEqual(result, "")

    def test_description_only(self):
        """Test extraction of a simple description without any sections."""
        docstring = "This is a simple description without any sections."
        result = extract_description_from_docstring(docstring)
        self.assertEqual(result, "This is a simple description without any sections.")

    def test_multiline_description_only(self):
        """Test extraction of a multi-line description without any sections."""
        docstring = """This is a multi-line description.

It has multiple paragraphs and line breaks.
But no Args or Returns sections."""
        result = extract_description_from_docstring(docstring)
        expected = """This is a multi-line description.

It has multiple paragraphs and line breaks.
But no Args or Returns sections."""
        self.assertEqual(result, expected)

    def test_description_with_args(self):
        """Test extraction strips Args section."""
        docstring = """This is the description.

Args:
    param1: First parameter.
    param2: Second parameter."""
        result = extract_description_from_docstring(docstring)
        self.assertEqual(result, "This is the description.")

    def test_description_with_returns(self):
        """Test extraction strips Returns section."""
        docstring = """This is the description.

Returns:
    Some return value."""
        result = extract_description_from_docstring(docstring)
        self.assertEqual(result, "This is the description.")

    def test_description_with_raises(self):
        """Test extraction strips Raises section."""
        docstring = """This is the description.

Raises:
    ValueError: When something goes wrong."""
        result = extract_description_from_docstring(docstring)
        self.assertEqual(result, "This is the description.")

    def test_description_with_multiple_sections(self):
        """Test extraction strips multiple sections (Args, Returns, Raises)."""
        docstring = """This is the description.
It can be multiple lines.

Args:
    param1: First parameter.
    param2: Second parameter.

Returns:
    Some return value.

Raises:
    ValueError: When something goes wrong.
    TypeError: When types don't match."""
        result = extract_description_from_docstring(docstring)
        expected = """This is the description.
It can be multiple lines."""
        self.assertEqual(result, expected)

    def test_description_with_examples(self):
        """Test extraction strips Examples section."""
        docstring = """This is the description.

Examples:
    >>> func(1, 2)
    3"""
        result = extract_description_from_docstring(docstring)
        self.assertEqual(result, "This is the description.")

    def test_description_with_notes(self):
        """Test extraction strips Notes section."""
        docstring = """This is the description.

Notes:
    This is a note about the function."""
        result = extract_description_from_docstring(docstring)
        self.assertEqual(result, "This is the description.")

    def test_description_with_see_also(self):
        """Test extraction strips See Also section."""
        docstring = """This is the description.

See Also:
    related_function: A related function."""
        result = extract_description_from_docstring(docstring)
        self.assertEqual(result, "This is the description.")

    def test_alternative_section_names(self):
        """Test extraction handles alternative section names (Arguments, Return, etc.)."""
        docstring = """This is the description.

Arguments:
    param1: First parameter.

Return:
    Some return value."""
        result = extract_description_from_docstring(docstring)
        self.assertEqual(result, "This is the description.")

    def test_parameters_section(self):
        """Test extraction strips Parameters section."""
        docstring = """This is the description.

Parameters:
    param1: First parameter.
    param2: Second parameter."""
        result = extract_description_from_docstring(docstring)
        self.assertEqual(result, "This is the description.")

    def test_yields_section(self):
        """Test extraction strips Yields section."""
        docstring = """This is the description.

Yields:
    Items one at a time."""
        result = extract_description_from_docstring(docstring)
        self.assertEqual(result, "This is the description.")

    def test_whitespace_handling(self):
        """Test that leading and trailing whitespace is stripped."""
        docstring = """

This is the description with leading/trailing whitespace.

Args:
    param1: First parameter.
"""
        result = extract_description_from_docstring(docstring)
        self.assertEqual(result, "This is the description with leading/trailing whitespace.")

    def test_google_style_docstring(self):
        """Test extraction from a Google-style docstring."""
        docstring = """Convert tool to MCP tool, injecting LLM and logging interfaces.

This function performs wrapping and validation of the tool.

Args:
    tool: The tool description to convert.
    custom_llm: Optional custom LLM interface to inject.
    custom_embedding: Optional custom Embedding interface to inject.
    custom_logging: Optional custom Logging interface to inject.
    custom_metrics: Optional custom Metrics interface to inject.
    constants: Optional constant parameters to always provide to the tool.

Returns:
    FunctionTool: The converted MCP FunctionTool.

Raises:
    ValueError: If required interfaces are missing."""
        result = extract_description_from_docstring(docstring)
        expected = """Convert tool to MCP tool, injecting LLM and logging interfaces.

This function performs wrapping and validation of the tool."""
        self.assertEqual(result, expected)

    def test_numpy_style_docstring(self):
        """Test extraction from a NumPy-style docstring (common parameters heading)."""
        docstring = """This is the description.

It can be multiple lines in the description.

Parameters
----------
param1 : int
    First parameter.
param2 : str
    Second parameter."""
        result = extract_description_from_docstring(docstring)
        # Note: This function is designed for Google-style docstrings with "Parameters:"
        # NumPy style uses "Parameters" without colon, so it may not be stripped
        expected = """This is the description.

It can be multiple lines in the description.

Parameters
----------
param1 : int
    First parameter.
param2 : str
    Second parameter."""
        self.assertEqual(result, expected)

    def test_section_at_beginning(self):
        """Test that sections at the very beginning result in empty description."""
        docstring = """Args:
    param1: First parameter."""
        result = extract_description_from_docstring(docstring)
        self.assertEqual(result, "")

    def test_indented_description(self):
        """Test extraction preserves indentation in the description."""
        docstring = """    This is an indented description.
It has multiple lines.

Args:
    param1: First parameter."""
        result = extract_description_from_docstring(docstring)
        # Note: The strip() call removes leading/trailing whitespace
        expected = """This is an indented description.
It has multiple lines."""
        self.assertEqual(result, expected)
