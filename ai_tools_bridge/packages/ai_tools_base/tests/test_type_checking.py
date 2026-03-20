import typing
from typing import Any
from unittest import TestCase

from pydantic import BaseModel

from ai_tools_base.type_checking import is_type_compatible


# Pydantic model hierarchy
class BaseResponse(BaseModel):
    status: str


class UserResponse(BaseResponse):
    user_id: int


class AdminResponse(UserResponse):
    permissions: list[str]


class ErrorResponse(BaseModel):
    error: str


class TestTypeChecking(TestCase):
    # === Direct equality ===
    def test_direct_match_primitives(self):
        assert is_type_compatible(int, int, strict=True)
        assert is_type_compatible(str, str, strict=True)
        assert is_type_compatible(float, float, strict=True)
        assert is_type_compatible(bool, bool, strict=True)
        assert is_type_compatible(type(None), type(None), strict=True)

    def test_direct_match_collections(self):
        assert is_type_compatible(dict, dict, strict=True)
        assert is_type_compatible(list, list, strict=True)
        assert is_type_compatible(set, set, strict=True)
        assert is_type_compatible(tuple, tuple, strict=True)

    def test_direct_match_pydantic(self):
        assert is_type_compatible(BaseResponse, BaseResponse, strict=True)
        assert is_type_compatible(UserResponse, UserResponse, strict=True)

    # === Subclass relationships (Pydantic inheritance) ===
    def test_pydantic_subclass_to_base(self):
        """Tool returns specialized model, post processor accepts base model."""
        assert is_type_compatible(UserResponse, BaseResponse, strict=True)
        assert is_type_compatible(AdminResponse, BaseResponse, strict=True)
        assert is_type_compatible(AdminResponse, UserResponse, strict=True)

    def test_pydantic_base_to_subclass_should_fail(self):
        """Base model cannot satisfy a more specific type requirement."""
        assert not is_type_compatible(BaseResponse, UserResponse, strict=True)
        assert not is_type_compatible(UserResponse, AdminResponse, strict=True)

    def test_pydantic_unrelated_models_should_fail(self):
        """Unrelated models are not compatible."""
        assert not is_type_compatible(UserResponse, ErrorResponse, strict=True)
        assert not is_type_compatible(ErrorResponse, BaseResponse, strict=True)

    # === Union types ===
    def test_type_in_union(self):
        """Return type is one member of the input union."""
        assert is_type_compatible(int, int | str, strict=True)
        assert is_type_compatible(str, int | str, strict=True)
        assert is_type_compatible(UserResponse, UserResponse | ErrorResponse, strict=True)

    def test_type_not_in_union(self):
        """Return type is not in the union."""
        assert not is_type_compatible(float, int | str, strict=True)

    def test_subclass_matches_union_member(self):
        """Return type is subclass of a union member."""
        assert is_type_compatible(UserResponse, BaseResponse | ErrorResponse, strict=True)
        assert is_type_compatible(AdminResponse, BaseResponse | ErrorResponse, strict=True)

    def test_union_equality(self):
        """Two identical unions (order independent)."""
        assert is_type_compatible(int | str, str | int, strict=True)
        assert is_type_compatible(UserResponse | ErrorResponse, ErrorResponse | UserResponse, strict=True)

    def test_union_to_non_union_should_fail(self):
        """A union type cannot satisfy a single type requirement."""
        assert not is_type_compatible(int | str, int, strict=True)
        assert not is_type_compatible(UserResponse | ErrorResponse, BaseResponse, strict=True)

    def test_none_in_union(self):
        """Optional types (unions with None)."""
        assert is_type_compatible(str, str | None, strict=True)
        assert is_type_compatible(type(None), str | None, strict=True)
        assert is_type_compatible(UserResponse, UserResponse | None, strict=True)

    # === Generic types (dict, list, etc.) ===
    def test_parameterized_to_bare(self):
        """Parameterized generic is compatible with bare generic."""
        assert is_type_compatible(dict[str, Any], dict, strict=True)
        assert is_type_compatible(dict[str, int], dict, strict=True)
        assert is_type_compatible(list[str], list, strict=True)
        assert is_type_compatible(list[int], list, strict=True)
        assert is_type_compatible(set[str], set, strict=True)

    def test_bare_to_parameterized_should_fail(self):
        """Bare generic is NOT compatible with parameterized (less specific)."""
        assert not is_type_compatible(dict, dict[str, Any], strict=True)
        assert not is_type_compatible(list, list[int], strict=True)

    def test_same_parameterized_generics(self):
        """Same parameterized generics are compatible."""
        assert is_type_compatible(dict[str, Any], dict[str, Any], strict=True)
        assert is_type_compatible(list[int], list[int], strict=True)

    def test_different_parameterized_same_origin(self):
        """Different type args but same origin - treated as compatible."""
        assert is_type_compatible(dict[str, int], dict[str, Any], strict=True)
        assert is_type_compatible(list[str], list[int], strict=True)

    def test_parameterized_in_union(self):
        """Parameterized generic in a union."""
        assert is_type_compatible(dict[str, Any], dict[str, Any] | None, strict=True)
        assert is_type_compatible(list[int], list[int] | str, strict=True)

    # === Mixed: Pydantic + Union ===
    def test_pydantic_subclass_in_union_with_base(self):
        """Subclass matches base class in union."""
        assert is_type_compatible(AdminResponse, BaseResponse | None, strict=True)
        assert is_type_compatible(UserResponse, BaseResponse | ErrorResponse | None, strict=True)

    # === Edge cases ===
    def test_nested_unions(self):
        """Nested union types (flattened in Python 3.10+)."""
        assert is_type_compatible(int, (int | str) | float, strict=True)

    def test_primitive_subclass(self):
        """bool is subclass of int."""
        assert is_type_compatible(bool, int, strict=True)
        assert not is_type_compatible(int, bool, strict=True)

    # === typing.Union vs | syntax ===
    # These tests verify backwards compatibility with deprecated typing.Union/Optional
    # which may still be used in user code
    def test_typing_union_type_in_union(self):
        """Return type is one member of a typing.Union."""
        assert is_type_compatible(int, typing.Union[int, str], strict=True)  # pyright: ignore[reportDeprecated]
        assert is_type_compatible(str, typing.Union[int, str], strict=True)  # pyright: ignore[reportDeprecated]
        assert is_type_compatible(UserResponse, typing.Union[UserResponse, ErrorResponse], strict=True)  # pyright: ignore[reportDeprecated]

    def test_typing_union_subclass_matches_member(self):
        """Return type is subclass of a typing.Union member."""
        assert is_type_compatible(UserResponse, typing.Union[BaseResponse, ErrorResponse], strict=True)  # pyright: ignore[reportDeprecated]
        assert is_type_compatible(AdminResponse, typing.Union[BaseResponse, ErrorResponse], strict=True)  # pyright: ignore[reportDeprecated]

    def test_optional_type(self):
        """Optional[X] is Union[X, None]."""
        assert is_type_compatible(str, typing.Optional[str], strict=True)  # pyright: ignore[reportDeprecated]
        assert is_type_compatible(type(None), typing.Optional[str], strict=True)  # pyright: ignore[reportDeprecated]
        assert is_type_compatible(UserResponse, typing.Optional[UserResponse], strict=True)  # pyright: ignore[reportDeprecated]

    def test_optional_with_subclass(self):
        """Subclass is compatible with Optional[BaseClass]."""
        assert is_type_compatible(UserResponse, typing.Optional[BaseResponse], strict=True)  # pyright: ignore[reportDeprecated]
        assert is_type_compatible(AdminResponse, typing.Optional[BaseResponse], strict=True)  # pyright: ignore[reportDeprecated]

    def test_typing_union_with_generics(self):
        """typing.Union with generic types."""
        assert is_type_compatible(dict[str, Any], typing.Union[dict[str, Any], None], strict=True)  # pyright: ignore[reportDeprecated]
        assert is_type_compatible(list[int], typing.Union[list[int], str], strict=True)  # pyright: ignore[reportDeprecated]

    # === Non-strict mode (strict=False) ===
    # These tests verify the non-strict mode used for constants validation
    # where runtime types (bare) need to match parameterized annotations

    def test_non_strict_bare_list_to_parameterized(self):
        """In non-strict mode, bare list is compatible with list[str].

        This is the primary use case: type(["ops_board"]) returns list,
        but the annotation is list[str]. At runtime we can't know the
        parameterized type, so non-strict mode allows this.
        """
        assert is_type_compatible(list, list[str], strict=False)
        assert is_type_compatible(list, list[int], strict=False)
        assert is_type_compatible(list, list[Any], strict=False)

    def test_non_strict_bare_dict_to_parameterized(self):
        """In non-strict mode, bare dict is compatible with dict[str, Any]."""
        assert is_type_compatible(dict, dict[str, Any], strict=False)
        assert is_type_compatible(dict, dict[str, int], strict=False)
        assert is_type_compatible(dict, dict[int, str], strict=False)

    def test_non_strict_bare_set_to_parameterized(self):
        """In non-strict mode, bare set is compatible with set[str]."""
        assert is_type_compatible(set, set[str], strict=False)
        assert is_type_compatible(set, set[int], strict=False)

    def test_non_strict_bare_tuple_to_parameterized(self):
        """In non-strict mode, bare tuple is compatible with tuple[str, ...]."""
        assert is_type_compatible(tuple, tuple[str, ...], strict=False)
        assert is_type_compatible(tuple, tuple[int, str], strict=False)

    def test_non_strict_with_union_containing_parameterized(self):
        """In non-strict mode, bare type matches parameterized type in union.

        This covers the exact error case: list[str] | None annotation
        with a runtime type of list.
        """
        assert is_type_compatible(list, list[str] | None, strict=False)
        assert is_type_compatible(dict, dict[str, Any] | None, strict=False)
        assert is_type_compatible(set, set[int] | str, strict=False)

    def test_non_strict_none_still_matches_optional(self):
        """Non-strict mode doesn't affect None matching Optional."""
        assert is_type_compatible(type(None), list[str] | None, strict=False)
        assert is_type_compatible(type(None), str | None, strict=False)

    def test_non_strict_incompatible_types_still_fail(self):
        """Non-strict mode doesn't make unrelated types compatible."""
        assert not is_type_compatible(list, dict[str, Any], strict=False)
        assert not is_type_compatible(dict, list[str], strict=False)
        assert not is_type_compatible(str, list[str], strict=False)
        assert not is_type_compatible(int, dict[str, Any], strict=False)

    def test_non_strict_subclass_bare_to_parameterized(self):
        """Non-strict mode works with subclass relationships."""
        # bool is subclass of int, but list[bool] origin is list
        assert is_type_compatible(list, list[int], strict=False)

    def test_strict_mode_still_rejects_bare_to_parameterized(self):
        """Confirm strict mode still rejects bare to parameterized."""
        assert not is_type_compatible(list, list[str], strict=True)
        assert not is_type_compatible(dict, dict[str, Any], strict=True)
        assert not is_type_compatible(set, set[int], strict=True)

    def test_non_strict_typing_optional_with_parameterized(self):
        """Non-strict mode works with typing.Optional containing parameterized types."""
        assert is_type_compatible(list, typing.Optional[list[str]], strict=False)  # pyright: ignore[reportDeprecated]
        assert is_type_compatible(dict, typing.Optional[dict[str, int]], strict=False)  # pyright: ignore[reportDeprecated]

    def test_non_strict_typing_union_with_parameterized(self):
        """Non-strict mode works with typing.Union containing parameterized types."""
        assert is_type_compatible(list, typing.Union[list[str], None], strict=False)  # pyright: ignore[reportDeprecated]
        assert is_type_compatible(dict, typing.Union[dict[str, Any], str], strict=False)  # pyright: ignore[reportDeprecated]
