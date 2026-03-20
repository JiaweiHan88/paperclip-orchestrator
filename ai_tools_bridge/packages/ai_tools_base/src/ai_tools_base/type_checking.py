import types
import typing
from typing import Any, get_args, get_origin


def _is_union_type(origin: Any, tp: Any) -> bool:
    """Check if a type is a union (typing.Union or types.UnionType from | syntax)."""
    # types.UnionType is the | syntax in Python 3.10+
    # typing.Union is the typing.Union[...] syntax (deprecated but still used in legacy code)
    return (
        origin is typing.Union  # pyright: ignore[reportDeprecated]
        or origin is types.UnionType
        or isinstance(tp, types.UnionType)
    )


def is_type_compatible(return_type: Any, input_type: Any, strict: bool) -> bool:
    """Check if return_type is compatible with input_type.

    Handles:
    - Direct type equality
    - Union types (return_type is a member of the union) - both typing.Union and | syntax
    - Subclass relationships (return_type is a subclass of input_type)
    - Generic types (e.g., dict[str, Any] is compatible with dict)
    """
    # Direct match
    if return_type == input_type:
        return True

    # Get origins for generic types (e.g., dict[str, Any] -> dict)
    return_origin = get_origin(return_type)
    input_origin = get_origin(input_type)

    # Check if input_type is a Union (typing.Union or | syntax)
    if _is_union_type(input_origin, input_type):
        union_args = get_args(input_type)
        return any(is_type_compatible(return_type, arg, strict=strict) for arg in union_args)

    # Handle generic type comparisons (e.g., dict[str, Any] vs dict)
    # Case 1: return is parameterized, input is bare (dict[str, Any] -> dict)
    if return_origin is not None and input_origin is None:
        if isinstance(input_type, type) and isinstance(return_origin, type):
            return issubclass(return_origin, input_type)

    # Case 2: both are parameterized - compare origins (dict[str, Any] -> dict[str, str])
    if return_origin is not None and input_origin is not None:
        if return_origin == input_origin:
            # Same origin, could add arg checking here if needed
            # For now, trust that same origin is compatible
            return True
        if isinstance(return_origin, type) and isinstance(input_origin, type):
            return issubclass(return_origin, input_origin)

    # Case 3: return is bare, input is parameterized (dict -> dict[str, Any])
    if not strict and return_origin is None and input_origin is not None:
        if isinstance(return_type, type) and isinstance(input_origin, type):
            return issubclass(return_type, input_origin)

    # Check subclass relationship for non-generic class types
    if isinstance(return_type, type) and isinstance(input_type, type):
        return issubclass(return_type, input_type)

    return False
