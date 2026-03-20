"""Tests for default post processors."""

import json
from datetime import datetime, timedelta
from typing import Any
from unittest import TestCase
from uuid import UUID, uuid4

from pydantic import BaseModel

from ai_tools_base.default_post_processors import (
    convert_to_json,
    convert_to_markdown,
    to_json,
    to_markdown,
)


# === Test Models ===
class SimpleModel(BaseModel):
    name: str
    value: int


class NestedModel(BaseModel):
    id: int
    child: SimpleModel


class ModelWithComplexTypes(BaseModel):
    task_id: UUID
    created_at: datetime
    duration: timedelta
    tags: list[str]
    metadata: dict[str, Any]
    optional_field: str | None


class ModelWithNestedList(BaseModel):
    items: list[SimpleModel]


class TestToJsonPostProcessor(TestCase):
    """Tests for the JSON post processor."""

    # === PostProcessor instance tests ===
    def test_post_processor_instance_exists(self):
        """The to_json PostProcessor instance should be properly configured."""
        assert to_json.name == "json"
        assert to_json.func is convert_to_json

    # === Pydantic model tests ===
    def test_simple_pydantic_model(self):
        """Simple Pydantic model should serialize to JSON."""
        model = SimpleModel(name="test", value=42)
        result = convert_to_json(model)
        parsed = json.loads(result)

        assert parsed == {"name": "test", "value": 42}

    def test_nested_pydantic_model(self):
        """Nested Pydantic models should serialize correctly."""
        model = NestedModel(id=1, child=SimpleModel(name="child", value=10))
        result = convert_to_json(model)
        parsed = json.loads(result)

        assert parsed == {"id": 1, "child": {"name": "child", "value": 10}}

    def test_pydantic_model_with_uuid(self):
        """UUID fields should serialize to string."""
        test_uuid = uuid4()
        model = ModelWithComplexTypes(
            task_id=test_uuid,
            created_at=datetime(2025, 1, 1, 12, 0, 0),
            duration=timedelta(hours=1),
            tags=[],
            metadata={},
            optional_field=None,
        )
        result = convert_to_json(model)
        parsed = json.loads(result)

        assert parsed["task_id"] == str(test_uuid)

    def test_pydantic_model_with_datetime(self):
        """Datetime fields should serialize to ISO format."""
        model = ModelWithComplexTypes(
            task_id=uuid4(),
            created_at=datetime(2025, 6, 15, 14, 30, 0),
            duration=timedelta(hours=1),
            tags=[],
            metadata={},
            optional_field=None,
        )
        result = convert_to_json(model)
        parsed = json.loads(result)

        assert parsed["created_at"] == "2025-06-15T14:30:00"

    def test_pydantic_model_with_timedelta(self):
        """Timedelta fields should serialize to ISO duration format."""
        model = ModelWithComplexTypes(
            task_id=uuid4(),
            created_at=datetime.now(),
            duration=timedelta(hours=2, minutes=30),
            tags=[],
            metadata={},
            optional_field=None,
        )
        result = convert_to_json(model)
        parsed = json.loads(result)

        assert parsed["duration"] == "PT2H30M"

    def test_pydantic_model_with_none(self):
        """None values should serialize to null."""
        model = ModelWithComplexTypes(
            task_id=uuid4(),
            created_at=datetime.now(),
            duration=timedelta(hours=1),
            tags=[],
            metadata={},
            optional_field=None,
        )
        result = convert_to_json(model)
        parsed = json.loads(result)

        assert parsed["optional_field"] is None

    def test_pydantic_model_with_nested_dict(self):
        """Nested dictionaries should serialize correctly."""
        model = ModelWithComplexTypes(
            task_id=uuid4(),
            created_at=datetime.now(),
            duration=timedelta(hours=1),
            tags=["a", "b"],
            metadata={"key": "value", "nested": {"deep": 123}},
            optional_field="present",
        )
        result = convert_to_json(model)
        parsed = json.loads(result)

        assert parsed["metadata"] == {"key": "value", "nested": {"deep": 123}}
        assert parsed["tags"] == ["a", "b"]
        assert parsed["optional_field"] == "present"

    # === List tests ===
    def test_list_of_dicts(self):
        """List of dictionaries should serialize correctly."""
        data = [{"a": 1}, {"b": 2}]
        result = convert_to_json(data)
        parsed = json.loads(result)

        assert parsed == [{"a": 1}, {"b": 2}]

    def test_list_of_primitives(self):
        """List of primitives should serialize correctly."""
        data = [1, 2, 3, "four", True, None]
        result = convert_to_json(data)
        parsed = json.loads(result)

        assert parsed == [1, 2, 3, "four", True, None]

    def test_empty_list(self):
        """Empty list should serialize to empty JSON array."""
        result = convert_to_json([])
        assert result == "[]"

    def test_mixed_list_with_datetime(self):
        """List with non-serializable types should use default=str."""
        now = datetime.now()
        data = [1, now, "text"]
        result = convert_to_json(data)
        parsed = json.loads(result)

        assert parsed[0] == 1
        assert parsed[1] == str(now)
        assert parsed[2] == "text"

    # === Dict tests ===
    def test_simple_dict(self):
        """Simple dictionary should serialize correctly."""
        data = {"key": "value", "number": 42}
        result = convert_to_json(data)
        parsed = json.loads(result)

        assert parsed == {"key": "value", "number": 42}

    def test_dict_with_datetime(self):
        """Dictionary with datetime should use default=str."""
        now = datetime(2025, 1, 1, 12, 0, 0)
        data = {"timestamp": now}
        result = convert_to_json(data)
        parsed = json.loads(result)

        assert parsed["timestamp"] == str(now)

    def test_nested_dict(self):
        """Nested dictionaries should serialize correctly."""
        data = {"outer": {"inner": {"deep": "value"}}}
        result = convert_to_json(data)
        parsed = json.loads(result)

        assert parsed == {"outer": {"inner": {"deep": "value"}}}

    def test_empty_dict(self):
        """Empty dictionary should serialize to empty JSON object."""
        result = convert_to_json({})
        assert result == "{}"

    # === Primitive tests ===
    def test_string(self):
        """String should serialize correctly."""
        result = convert_to_json("hello world")
        assert json.loads(result) == "hello world"

    def test_integer(self):
        """Integer should serialize correctly."""
        result = convert_to_json(42)
        assert json.loads(result) == 42

    def test_float(self):
        """Float should serialize correctly."""
        result = convert_to_json(3.14)
        assert json.loads(result) == 3.14

    def test_boolean_true(self):
        """Boolean True should serialize correctly."""
        result = convert_to_json(True)
        assert json.loads(result) is True

    def test_boolean_false(self):
        """Boolean False should serialize correctly."""
        result = convert_to_json(False)
        assert json.loads(result) is False

    def test_none(self):
        """None should serialize to null."""
        result = convert_to_json(None)
        assert json.loads(result) is None

    # === Formatting tests ===
    def test_json_is_indented(self):
        """JSON output should be indented with 2 spaces."""
        data = {"key": "value"}
        result = convert_to_json(data)
        assert "  " in result  # Should have indentation


class TestToMarkdownPostProcessor(TestCase):
    """Tests for the Markdown post processor."""

    # === PostProcessor instance tests ===
    def test_post_processor_instance_exists(self):
        """The to_markdown PostProcessor instance should be properly configured."""
        assert to_markdown.name == "markdown"
        assert to_markdown.func is convert_to_markdown

    # === Pydantic model tests ===
    def test_simple_pydantic_model(self):
        """Simple Pydantic model should convert to markdown."""
        model = SimpleModel(name="test", value=42)
        result = convert_to_markdown(model)

        assert "**name:** test" in result
        assert "**value:** 42" in result

    def test_pydantic_model_with_list(self):
        """Model with list should show bullet points."""
        model = ModelWithComplexTypes(
            task_id=uuid4(),
            created_at=datetime.now(),
            duration=timedelta(hours=1),
            tags=["python", "testing", "markdown"],
            metadata={},
            optional_field=None,
        )
        result = convert_to_markdown(model)

        assert "**tags:**" in result
        assert "  - python" in result
        assert "  - testing" in result
        assert "  - markdown" in result

    def test_pydantic_model_with_nested_dict(self):
        """Model with nested dict should show JSON inline."""
        model = ModelWithComplexTypes(
            task_id=uuid4(),
            created_at=datetime.now(),
            duration=timedelta(hours=1),
            tags=[],
            metadata={"key": "value"},
            optional_field=None,
        )
        result = convert_to_markdown(model)

        assert '**metadata:** {"key": "value"}' in result

    def test_pydantic_model_with_none(self):
        """None values should display as None."""
        model = ModelWithComplexTypes(
            task_id=uuid4(),
            created_at=datetime.now(),
            duration=timedelta(hours=1),
            tags=[],
            metadata={},
            optional_field=None,
        )
        result = convert_to_markdown(model)

        assert "**optional_field:** None" in result

    def test_pydantic_model_with_nested_models_in_list(self):
        """Nested Pydantic models in list should show as JSON."""
        model = ModelWithNestedList(
            items=[
                SimpleModel(name="first", value=1),
                SimpleModel(name="second", value=2),
            ]
        )
        result = convert_to_markdown(model)

        assert "**items:**" in result
        assert '{"name": "first", "value": 1}' in result
        assert '{"name": "second", "value": 2}' in result

    # === Dict tests ===
    def test_simple_dict(self):
        """Simple dictionary should convert to markdown."""
        data = {"name": "test", "count": 5}
        result = convert_to_markdown(data)

        assert "**name:** test" in result
        assert "**count:** 5" in result

    def test_dict_with_list(self):
        """Dictionary with list should show bullet points."""
        data = {"items": ["a", "b", "c"]}
        result = convert_to_markdown(data)

        assert "**items:**" in result
        assert "  - a" in result
        assert "  - b" in result
        assert "  - c" in result

    def test_dict_with_nested_dict(self):
        """Dictionary with nested dict should show JSON inline."""
        data = {"config": {"debug": True, "level": 5}}
        result = convert_to_markdown(data)

        assert '**config:** {"debug": true, "level": 5}' in result

    def test_dict_with_list_of_dicts(self):
        """Dictionary with list of dicts should show JSON per item."""
        data = {"users": [{"name": "Alice"}, {"name": "Bob"}]}
        result = convert_to_markdown(data)

        assert "**users:**" in result
        assert '{"name": "Alice"}' in result
        assert '{"name": "Bob"}' in result

    def test_empty_dict(self):
        """Empty dictionary should produce empty string."""
        result = convert_to_markdown({})
        assert result == ""

    def test_empty_list_value(self):
        """Empty list value should show header with no items."""
        data: dict[str, Any] = {"items": []}
        result = convert_to_markdown(data)

        assert "**items:**" in result
        assert "  -" not in result

    # === Formatting tests ===
    def test_output_is_valid_markdown(self):
        """Output should be valid markdown with bold keys."""
        data = {"key": "value"}
        result = convert_to_markdown(data)

        assert result.startswith("**")
        assert ":** " in result

    def test_multiple_fields_on_separate_lines(self):
        """Each field should be on a separate line."""
        data = {"a": 1, "b": 2, "c": 3}
        result = convert_to_markdown(data)
        lines = result.split("\n")

        assert len(lines) == 3

    # === Type handling tests ===
    def test_boolean_values(self):
        """Boolean values should display correctly."""
        data = {"enabled": True, "disabled": False}
        result = convert_to_markdown(data)

        assert "**enabled:** True" in result
        assert "**disabled:** False" in result

    def test_numeric_values(self):
        """Numeric values should display correctly."""
        data = {"integer": 42, "float": 3.14}
        result = convert_to_markdown(data)

        assert "**integer:** 42" in result
        assert "**float:** 3.14" in result

    def test_datetime_value(self):
        """Datetime values should display as string representation."""
        now = datetime(2025, 6, 15, 14, 30, 0)
        model = ModelWithComplexTypes(
            task_id=uuid4(),
            created_at=now,
            duration=timedelta(hours=1),
            tags=[],
            metadata={},
            optional_field=None,
        )
        result = convert_to_markdown(model)

        # Pydantic model_dump() converts datetime to datetime object
        # which then gets str() representation
        assert "**created_at:**" in result
        assert "2025-06-15" in result

    # === List tests ===
    def test_list_of_primitives(self):
        """List of primitives should show as bullet points."""
        result = convert_to_markdown(["apple", "banana", "cherry"])

        assert "- apple" in result
        assert "- banana" in result
        assert "- cherry" in result

    def test_list_of_dicts(self):
        """List of dicts should show as JSON bullet points."""
        data = [{"name": "Alice"}, {"name": "Bob"}]
        result = convert_to_markdown(data)

        assert '- {"name": "Alice"}' in result
        assert '- {"name": "Bob"}' in result

    def test_list_of_pydantic_models(self):
        """List of Pydantic models should show as JSON bullet points."""
        models = [
            SimpleModel(name="first", value=1),
            SimpleModel(name="second", value=2),
        ]
        result = convert_to_markdown(models)

        assert '- {"name": "first", "value": 1}' in result
        assert '- {"name": "second", "value": 2}' in result

    def test_empty_list(self):
        """Empty list should produce empty string."""
        result = convert_to_markdown([])
        assert result == ""

    def test_list_of_numbers(self):
        """List of numbers should show as bullet points."""
        result = convert_to_markdown([1, 2, 3])

        assert "- 1" in result
        assert "- 2" in result
        assert "- 3" in result

    # === Primitive tests ===
    def test_string_primitive(self):
        """String should return as-is."""
        result = convert_to_markdown("hello world")
        assert result == "hello world"

    def test_integer_primitive(self):
        """Integer should return as string."""
        result = convert_to_markdown(42)
        assert result == "42"

    def test_float_primitive(self):
        """Float should return as string."""
        result = convert_to_markdown(3.14)
        assert result == "3.14"

    def test_boolean_true_primitive(self):
        """Boolean True should return as 'True'."""
        result = convert_to_markdown(True)
        assert result == "True"

    def test_boolean_false_primitive(self):
        """Boolean False should return as 'False'."""
        result = convert_to_markdown(False)
        assert result == "False"

    def test_none_primitive(self):
        """None should return as 'None'."""
        result = convert_to_markdown(None)
        assert result == "None"
