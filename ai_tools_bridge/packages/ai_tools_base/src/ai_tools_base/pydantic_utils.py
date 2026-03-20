from pydantic import BaseModel, create_model


def combine_base_models(
    model_name: str,
    *args: type[BaseModel],
) -> type[BaseModel]:
    """Combine multiple Pydantic BaseModel classes into a new one.

    Uses multiple inheritance via `__base__` to properly inherit
    validators, configuration, and methods from all base models.

    Args:
        model_name: The name of the new combined model.
        *args: BaseModel classes to combine.

    Returns:
        A new BaseModel class that inherits from all provided models.

    Raises:
        ValueError: If duplicate field names are found across the base models.
    """
    # Check for duplicate field names across all base models
    seen_fields: dict[str, str] = {}  # field_name -> model_name
    for base_model in args:
        for field_name in base_model.model_fields:
            if field_name in seen_fields:
                raise ValueError(
                    f"Duplicate field '{field_name}' found in '{base_model.__name__}' "
                    f"(already defined in '{seen_fields[field_name]}')"
                )
            seen_fields[field_name] = base_model.__name__

    return create_model(model_name, __base__=args)
