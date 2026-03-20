import inspect
from collections.abc import Callable
from typing import Any, get_origin

from pydantic import BaseModel
from pydantic.fields import FieldInfo
from pydantic_core import PydanticUndefined

# Mutable container types that commonly use None default pattern
CONTAINER_TYPES = (list, dict, set)

# Common section headers in docstrings (Google style and others)
DOCSTRING_SECTION_HEADERS = [
    "Args:",
    "Arguments:",
    "Parameters:",
    "Params:",
    "Returns:",
    "Return:",
    "Yields:",
    "Yield:",
    "Raises:",
    "Raise:",
    "Examples:",
    "Example:",
    "Note:",
    "Notes:",
    "See Also:",
    "References:",
    "Attributes:",
    "Methods:",
]


def extract_description_from_docstring(docstring: str | None) -> str:
    """Extract only the description part from a docstring.

    Removes Args, Returns, Raises, and other sections, keeping only the initial description.
    Also cleans up indentation using inspect.cleandoc.

    Args:
        docstring: The full docstring to extract from.

    Returns:
        The description part only, stripped of all section headers and their content.
    """
    if not docstring:
        return ""

    cleaned = inspect.cleandoc(docstring)
    lines = cleaned.split("\n")
    description_lines: list[str] = []

    for line in lines:
        # Check if this line starts a section
        stripped = line.strip()
        if any(stripped.startswith(header) for header in DOCSTRING_SECTION_HEADERS):
            break
        description_lines.append(line)

    # Join and clean up
    description: str = "\n".join(description_lines).strip()
    return description


class SignatureValidationError(Exception):
    """Raised when a function signature does not match the expected schema."""


def _is_container_type(annotation: Any) -> bool:
    """Check if an annotation is a container type (list, dict, set, frozenset)."""
    origin = get_origin(annotation)
    if origin is not None:
        return origin in CONTAINER_TYPES
    return annotation in CONTAINER_TYPES


def _is_optional_container_pattern(sig_annotation: Any, sig_default: Any, schema_annotation: Any) -> bool:
    """Check if function uses the common 'Optional[ContainerType] = None' pattern for a container schema field.

    This is a valid pattern because Python best practices recommend avoiding mutable default arguments.
    Instead of `def f(items: list[str] = [])`, it's safer to use `def f(items: list[str] | None = None)`.

    Args:
        sig_annotation: The function parameter's type annotation
        sig_default: The function parameter's default value
        schema_annotation: The schema field's type annotation

    Returns:
        True if this is a valid optional container pattern match
    """
    # Function must have None as default
    if sig_default is not None:
        return False

    # Schema annotation must be a container type
    if not _is_container_type(schema_annotation):
        return False

    schema_annotation_optional = schema_annotation | None

    if schema_annotation_optional == sig_annotation:
        return True

    raise SignatureValidationError(
        f"Annotation mismatch for optional mutable parameter: "
        f"expected {schema_annotation_optional}, got {sig_annotation}"
    )


def field_info_to_parameter(name: str, field_info: FieldInfo) -> inspect.Parameter:
    """Convert Pydantic FieldInfo to inspect.Parameter."""
    default: Any = inspect.Parameter.empty
    if field_info.default is not PydanticUndefined:
        # Field has an explicit default (including None)
        default = field_info.default
    elif field_info.default_factory is not None:
        # Field has a default_factory
        default = field_info.default_factory()  # type: ignore[misc]

    param = inspect.Parameter(
        name=name,
        kind=inspect.Parameter.POSITIONAL_OR_KEYWORD,
        default=default,
        annotation=field_info.annotation,
    )
    return param


def schema_to_parameters(schema: type[BaseModel]) -> list[inspect.Parameter]:
    """Convert Pydantic schema to a list of inspect.Parameters.

    Parameters are sorted so that required parameters (no default) come before
    optional parameters (with default), ensuring a valid Python function signature.
    """
    parameters: list[inspect.Parameter] = []
    for field_name, model_field in schema.model_fields.items():
        param = field_info_to_parameter(field_name, model_field)
        parameters.append(param)

    # Sort: parameters without defaults first, then parameters with defaults
    parameters.sort(key=lambda p: p.default is not inspect.Parameter.empty)
    return parameters


def validate_function_signature_to_schema(fn: Callable[..., Any], schema: type[BaseModel]) -> None:
    """Check if a function's signature matches the parameters defined in a Pydantic schema.

    Args:
        fn: The function to validate.
        schema: The Pydantic schema to validate against.

    Raises:
        SignatureValidationError: If the function signature does not match the schema.
    """
    signature = inspect.signature(fn)

    for field_name, field_info in schema.model_fields.items():
        if field_name not in signature.parameters:
            raise SignatureValidationError(f"Parameter {field_name} not found in function signature.")

        sig_param = signature.parameters[field_name]
        schema_param = field_info_to_parameter(field_name, field_info)

        # Check for the common "Optional[ContainerType] = None" pattern
        # This is valid because it avoids mutable default argument pitfalls
        is_optional_container = _is_optional_container_pattern(
            sig_param.annotation,
            sig_param.default,
            schema_param.annotation,
        )

        if is_optional_container:
            # Skip annotation and default checks - this pattern is allowed
            continue

        # Check annotation
        if sig_param.annotation != schema_param.annotation:
            raise SignatureValidationError(
                f"Annotation mismatch for parameter {field_name}: "
                f"expected {schema_param.annotation}, got {sig_param.annotation}"
            )

        # Check default value
        if sig_param.default != schema_param.default:
            raise SignatureValidationError(
                f"Default value mismatch for parameter {field_name}: "
                f"expected {schema_param.default}, got {sig_param.default}"
            )


def apply_schema_to_function(
    fn: Callable[..., Any],
    schema: type[BaseModel],
    extra_params: dict[str, tuple[Any, Any]] | None = None,
) -> None:
    """Apply a Pydantic schema to a function, updating both signature and annotations.

    This modifies the function in-place to make it appear as if it has the parameters
    defined in the schema, which is necessary for Pydantic's TypeAdapter to work correctly.

    Args:
        fn: The function to modify.
        schema: The Pydantic schema defining the parameters.
        extra_params: Optional dictionary of additional parameters to add to the signature.
            These are NOT added to the schema, only to the function signature. Useful for
            parameters that will be provided as constants at runtime but aren't LLM-visible.
            Format: {param_name: (annotation, default)} where default can be ... for required.
    """
    # Also update __signature__ for inspect.signature() compatibility
    signature = inspect.signature(fn)

    parameters = schema_to_parameters(schema)

    # Add extra parameters if provided
    if extra_params:
        for param_name, (annotation, default) in extra_params.items():
            param_default = inspect.Parameter.empty if default is ... else default
            extra_param = inspect.Parameter(
                name=param_name,
                kind=inspect.Parameter.POSITIONAL_OR_KEYWORD,
                default=param_default,
                annotation=annotation,
            )
            parameters.append(extra_param)

        # Re-sort: parameters without defaults first, then parameters with defaults
        parameters.sort(key=lambda p: p.default is not inspect.Parameter.empty)

    new_signature = inspect.Signature(
        parameters=parameters,
        return_annotation=signature.return_annotation,
    )

    apply_signature_to_function(fn, new_signature)


def apply_signature_to_function(fn: Callable[..., Any], signature: inspect.Signature) -> None:
    """Apply an inspect.Signature to a function, updating both signature and annotations.

    This modifies the function in-place to make it appear as if it has the parameters
    defined in the signature.
    """
    # Update __annotations__
    new_annotations = {}
    for param in signature.parameters.values():
        new_annotations[param.name] = param.annotation

    # Preserve return annotation if it exists
    if "return" in fn.__annotations__:
        new_annotations["return"] = fn.__annotations__["return"]

    fn.__annotations__ = new_annotations

    # Update __signature__
    fn.__signature__ = signature  # type: ignore[attr-defined]
