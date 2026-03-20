"""Exhaustive test cases for combine_base_models function."""

import pytest
from pydantic import BaseModel, ConfigDict, Field, field_validator

from ai_tools_base.pydantic_utils import combine_base_models

# =============================================================================
# Test Models
# =============================================================================


class ModelA(BaseModel):
    """Simple model with basic fields."""

    field_a: str
    field_b: int


class ModelB(BaseModel):
    """Another simple model with different fields."""

    field_c: float
    field_d: bool


class ModelC(BaseModel):
    """Model with optional and default fields."""

    field_e: str | None = None
    field_f: int = 42


class ModelWithValidator(BaseModel):
    """Model with a field validator."""

    name: str

    @field_validator("name")
    @classmethod
    def name_must_be_uppercase(cls, v: str) -> str:
        return v.upper()


class ModelWithConfig(BaseModel):
    """Model with custom configuration."""

    model_config = ConfigDict(str_strip_whitespace=True)

    text: str


class ModelWithMethod(BaseModel):
    """Model with a custom method."""

    value: int

    def double(self) -> int:
        return self.value * 2


class ModelWithDuplicateFieldA(BaseModel):
    """Model with a field that will conflict."""

    duplicate_field: str


class ModelWithDuplicateFieldB(BaseModel):
    """Another model with the same conflicting field."""

    duplicate_field: int


class ModelWithAlias(BaseModel):
    """Model with field aliases."""

    internal_name: str = Field(alias="externalName")


class EmptyModel(BaseModel):
    """Model with no fields."""

    pass


class NestedModel(BaseModel):
    """Model with nested BaseModel field."""

    nested: ModelA


class ModelWithComplexTypes(BaseModel):
    """Model with complex type annotations."""

    items: list[str]
    mapping: dict[str, int]
    optional_list: list[int] | None = None


# =============================================================================
# Basic Functionality Tests
# =============================================================================


class TestCombineBaseModelsBasic:
    """Test basic functionality of combine_base_models."""

    def test_combine_two_simple_models(self) -> None:
        """Test combining two simple models."""
        Combined = combine_base_models("Combined", ModelA, ModelB)

        assert Combined.__name__ == "Combined"
        assert "field_a" in Combined.model_fields
        assert "field_b" in Combined.model_fields
        assert "field_c" in Combined.model_fields
        assert "field_d" in Combined.model_fields

    def test_combine_creates_valid_instance(self) -> None:
        """Test that combined model can be instantiated."""
        Combined = combine_base_models("Combined", ModelA, ModelB)

        instance = Combined(field_a="test", field_b=1, field_c=1.5, field_d=True)

        assert instance.field_a == "test"  # type: ignore[attr-defined]
        assert instance.field_b == 1  # type: ignore[attr-defined]
        assert instance.field_c == 1.5  # type: ignore[attr-defined]
        assert instance.field_d is True  # type: ignore[attr-defined]

    def test_combine_single_model(self) -> None:
        """Test combining a single model (edge case)."""
        Combined = combine_base_models("Combined", ModelA)

        assert "field_a" in Combined.model_fields
        assert "field_b" in Combined.model_fields

        instance = Combined(field_a="test", field_b=1)
        assert instance.field_a == "test"  # type: ignore[attr-defined]

    def test_combine_three_models(self) -> None:
        """Test combining three models."""
        Combined = combine_base_models("Combined", ModelA, ModelB, ModelC)

        assert len(Combined.model_fields) == 6
        assert "field_a" in Combined.model_fields
        assert "field_c" in Combined.model_fields
        assert "field_e" in Combined.model_fields

    def test_combine_no_models(self) -> None:
        """Test combining zero models raises an error."""
        with pytest.raises(TypeError):
            combine_base_models("Combined")

    def test_model_name_is_set_correctly(self) -> None:
        """Test that the model name is set correctly."""
        Combined = combine_base_models("MyCustomName", ModelA, ModelB)

        assert Combined.__name__ == "MyCustomName"


# =============================================================================
# Default and Optional Field Tests
# =============================================================================


class TestCombineBaseModelsDefaults:
    """Test handling of default and optional fields."""

    def test_preserves_default_values(self) -> None:
        """Test that default values are preserved."""
        Combined = combine_base_models("Combined", ModelA, ModelC)

        # Can create instance without optional/default fields from ModelC
        instance = Combined(field_a="test", field_b=1)

        assert instance.field_e is None  # type: ignore[attr-defined]
        assert instance.field_f == 42  # type: ignore[attr-defined]

    def test_override_default_values(self) -> None:
        """Test that default values can be overridden."""
        Combined = combine_base_models("Combined", ModelC)

        instance = Combined(field_e="provided", field_f=100)

        assert instance.field_e == "provided"  # type: ignore[attr-defined]
        assert instance.field_f == 100  # type: ignore[attr-defined]


# =============================================================================
# Validator Inheritance Tests
# =============================================================================


class TestCombineBaseModelsValidators:
    """Test that validators are inherited."""

    def test_validators_are_inherited(self) -> None:
        """Test that field validators are inherited from base models."""
        Combined = combine_base_models("Combined", ModelWithValidator, ModelA)

        instance = Combined(name="lowercase", field_a="test", field_b=1)

        # Validator should have converted to uppercase
        assert instance.name == "LOWERCASE"  # type: ignore[attr-defined]

    def test_multiple_validators_inherited(self) -> None:
        """Test multiple models with validators."""

        class AnotherValidator(BaseModel):
            value: int

            @field_validator("value")
            @classmethod
            def value_must_be_positive(cls, v: int) -> int:
                if v < 0:
                    raise ValueError("value must be positive")
                return v

        Combined = combine_base_models("Combined", ModelWithValidator, AnotherValidator)

        instance = Combined(name="test", value=10)
        assert instance.name == "TEST"  # type: ignore[attr-defined]
        assert instance.value == 10  # type: ignore[attr-defined]

        with pytest.raises(ValueError, match="value must be positive"):
            Combined(name="test", value=-1)


# =============================================================================
# Configuration Inheritance Tests
# =============================================================================


class TestCombineBaseModelsConfig:
    """Test that configuration is inherited."""

    def test_config_is_inherited(self) -> None:
        """Test that model config is inherited."""
        Combined = combine_base_models("Combined", ModelWithConfig, ModelA)

        instance = Combined(text="  stripped  ", field_a="test", field_b=1)

        # Config should strip whitespace
        assert instance.text == "stripped"  # type: ignore[attr-defined]


# =============================================================================
# Method Inheritance Tests
# =============================================================================


class TestCombineBaseModelsMethods:
    """Test that methods are inherited."""

    def test_methods_are_inherited(self) -> None:
        """Test that custom methods are inherited from base models."""
        Combined = combine_base_models("Combined", ModelWithMethod, ModelA)

        instance = Combined(value=5, field_a="test", field_b=1)

        assert instance.double() == 10  # type: ignore[attr-defined]

    def test_multiple_methods_inherited(self) -> None:
        """Test that methods from multiple models are inherited."""

        class ModelWithTriple(BaseModel):
            number: float

            def triple(self) -> float:
                return self.number * 3

        Combined = combine_base_models("Combined", ModelWithMethod, ModelWithTriple)

        instance = Combined(value=5, number=2.0)

        assert instance.double() == 10  # type: ignore[attr-defined]
        assert instance.triple() == 6.0  # type: ignore[attr-defined]


# =============================================================================
# Duplicate Field Detection Tests
# =============================================================================


class TestCombineBaseModelsDuplicates:
    """Test duplicate field detection."""

    def test_raises_on_duplicate_fields(self) -> None:
        """Test that ValueError is raised for duplicate field names."""
        with pytest.raises(ValueError) as exc_info:
            combine_base_models("Combined", ModelWithDuplicateFieldA, ModelWithDuplicateFieldB)

        error_message = str(exc_info.value)
        assert "duplicate_field" in error_message
        assert "ModelWithDuplicateFieldA" in error_message
        assert "ModelWithDuplicateFieldB" in error_message

    def test_raises_on_duplicate_with_multiple_models(self) -> None:
        """Test duplicate detection across multiple models."""

        class ModelX(BaseModel):
            unique_x: str

        class ModelY(BaseModel):
            shared: int

        class ModelZ(BaseModel):
            shared: str  # Duplicate with ModelY

        with pytest.raises(ValueError) as exc_info:
            combine_base_models("Combined", ModelX, ModelY, ModelZ)

        assert "shared" in str(exc_info.value)

    def test_no_error_for_unique_fields(self) -> None:
        """Test that no error is raised when all fields are unique."""
        # Should not raise
        Combined = combine_base_models("Combined", ModelA, ModelB, ModelC)
        assert Combined is not None


# =============================================================================
# Field Alias Tests
# =============================================================================


class TestCombineBaseModelsAliases:
    """Test handling of field aliases."""

    def test_preserves_field_aliases(self) -> None:
        """Test that field aliases are preserved."""
        Combined = combine_base_models("Combined", ModelWithAlias, ModelA)

        # Should accept alias
        instance = Combined(externalName="value", field_a="test", field_b=1)
        assert instance.internal_name == "value"  # type: ignore[attr-defined]

    def test_alias_in_json_schema(self) -> None:
        """Test that aliases appear in JSON schema."""
        Combined = combine_base_models("Combined", ModelWithAlias)

        schema = Combined.model_json_schema()
        properties = schema.get("properties", {})

        # The alias should be in the schema
        assert "externalName" in properties


# =============================================================================
# Empty Model Tests
# =============================================================================


class TestCombineBaseModelsEmpty:
    """Test handling of empty models."""

    def test_combine_with_empty_model(self) -> None:
        """Test combining with an empty model."""
        Combined = combine_base_models("Combined", ModelA, EmptyModel)

        # Should have only ModelA's fields
        assert len(Combined.model_fields) == 2
        assert "field_a" in Combined.model_fields
        assert "field_b" in Combined.model_fields

    def test_combine_only_empty_models(self) -> None:
        """Test combining two different empty models."""

        class EmptyModel2(BaseModel):
            pass

        Combined = combine_base_models("Combined", EmptyModel, EmptyModel2)

        assert len(Combined.model_fields) == 0


# =============================================================================
# Complex Type Tests
# =============================================================================


class TestCombineBaseModelsComplexTypes:
    """Test handling of complex type annotations."""

    def test_preserves_complex_types(self) -> None:
        """Test that complex type annotations are preserved."""
        Combined = combine_base_models("Combined", ModelWithComplexTypes, ModelA)

        instance = Combined(
            items=["a", "b"],
            mapping={"key": 1},
            field_a="test",
            field_b=1,
        )

        assert instance.items == ["a", "b"]  # type: ignore[attr-defined]
        assert instance.mapping == {"key": 1}  # type: ignore[attr-defined]
        assert instance.optional_list is None  # type: ignore[attr-defined]

    def test_nested_model_types(self) -> None:
        """Test that nested model types work correctly."""
        Combined = combine_base_models("Combined", NestedModel, ModelB)

        nested_data = ModelA(field_a="nested", field_b=99)
        instance = Combined(nested=nested_data, field_c=1.0, field_d=False)

        assert instance.nested.field_a == "nested"  # type: ignore[attr-defined]
        assert instance.nested.field_b == 99  # type: ignore[attr-defined]


# =============================================================================
# Inheritance Chain Tests
# =============================================================================


class TestCombineBaseModelsInheritance:
    """Test inheritance behavior."""

    def test_isinstance_checks(self) -> None:
        """Test that isinstance checks work for base models."""
        Combined = combine_base_models("Combined", ModelA, ModelB)

        instance = Combined(field_a="test", field_b=1, field_c=1.0, field_d=True)

        assert isinstance(instance, Combined)
        assert isinstance(instance, ModelA)
        assert isinstance(instance, ModelB)
        assert isinstance(instance, BaseModel)

    def test_issubclass_checks(self) -> None:
        """Test that issubclass checks work for base models."""
        Combined = combine_base_models("Combined", ModelA, ModelB)

        assert issubclass(Combined, ModelA)
        assert issubclass(Combined, ModelB)
        assert issubclass(Combined, BaseModel)


# =============================================================================
# Serialization Tests
# =============================================================================


class TestCombineBaseModelsSerialization:
    """Test serialization of combined models."""

    def test_model_dump(self) -> None:
        """Test that model_dump works correctly."""
        Combined = combine_base_models("Combined", ModelA, ModelB)

        instance = Combined(field_a="test", field_b=1, field_c=1.5, field_d=True)
        data = instance.model_dump()

        assert data == {
            "field_a": "test",
            "field_b": 1,
            "field_c": 1.5,
            "field_d": True,
        }

    def test_model_dump_json(self) -> None:
        """Test that model_dump_json works correctly."""
        Combined = combine_base_models("Combined", ModelA, ModelB)

        instance = Combined(field_a="test", field_b=1, field_c=1.5, field_d=True)
        json_str = instance.model_dump_json()

        assert '"field_a":"test"' in json_str
        assert '"field_b":1' in json_str

    def test_model_validate(self) -> None:
        """Test that model_validate works correctly."""
        Combined = combine_base_models("Combined", ModelA, ModelB)

        data = {"field_a": "test", "field_b": 1, "field_c": 1.5, "field_d": True}
        instance = Combined.model_validate(data)

        assert instance.field_a == "test"  # type: ignore[attr-defined]
        assert instance.field_d is True  # type: ignore[attr-defined]


# =============================================================================
# JSON Schema Tests
# =============================================================================


class TestCombineBaseModelsSchema:
    """Test JSON schema generation."""

    def test_json_schema_includes_all_fields(self) -> None:
        """Test that JSON schema includes all fields from combined models."""
        Combined = combine_base_models("Combined", ModelA, ModelB)

        schema = Combined.model_json_schema()
        properties = schema.get("properties", {})

        assert "field_a" in properties
        assert "field_b" in properties
        assert "field_c" in properties
        assert "field_d" in properties

    def test_json_schema_required_fields(self) -> None:
        """Test that required fields are correctly marked in schema."""
        Combined = combine_base_models("Combined", ModelA, ModelC)

        schema = Combined.model_json_schema()
        required = schema.get("required", [])

        # ModelA fields are required, ModelC has defaults
        assert "field_a" in required
        assert "field_b" in required
        assert "field_e" not in required
        assert "field_f" not in required


# =============================================================================
# Edge Cases
# =============================================================================


class TestCombineBaseModelsEdgeCases:
    """Test edge cases and unusual scenarios."""

    def test_same_model_twice(self) -> None:
        """Test combining the same model with itself."""
        # This should raise because all fields would be duplicates
        with pytest.raises(ValueError):
            combine_base_models("Combined", ModelA, ModelA)

    def test_model_with_private_attributes(self) -> None:
        """Test model with private attributes."""
        from pydantic import PrivateAttr

        class ModelWithPrivate(BaseModel):
            public: str
            _private: int = PrivateAttr(default=0)

        Combined = combine_base_models("Combined", ModelWithPrivate, ModelB)

        instance = Combined(public="test", field_c=1.0, field_d=True)
        assert instance.public == "test"  # type: ignore[attr-defined]
        assert instance._private == 0  # type: ignore[attr-defined]

    def test_deeply_nested_combination(self) -> None:
        """Test combining already combined models."""
        Combined1 = combine_base_models("Combined1", ModelA, ModelB)

        class ModelExtra(BaseModel):
            extra_field: str

        # Combine the combined model with another
        Combined2 = combine_base_models("Combined2", Combined1, ModelExtra)

        instance = Combined2(field_a="a", field_b=1, field_c=1.0, field_d=True, extra_field="extra")

        assert instance.field_a == "a"  # type: ignore[attr-defined]
        assert instance.extra_field == "extra"  # type: ignore[attr-defined]

    def test_special_field_names(self) -> None:
        """Test models with special but valid field names."""

        class SpecialNames(BaseModel):
            class_: str = Field(alias="class")
            type_: str = Field(alias="type")

        Combined = combine_base_models("Combined", SpecialNames, ModelA)

        # Using aliases
        instance = Combined(**{"class": "test", "type": "value", "field_a": "a", "field_b": 1})
        assert instance.class_ == "test"  # type: ignore[attr-defined]
        assert instance.type_ == "value"  # type: ignore[attr-defined]
