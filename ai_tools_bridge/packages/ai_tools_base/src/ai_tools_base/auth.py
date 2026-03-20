"""Authentication utilities for token retrieval from environment variables and .netrc files."""

import os
from netrc import netrc


def get_token(
    common_names: list[str] | str | None = None,
    env_names: list[str] | str | None = None,
    netrc_names: list[str] | str | None = None,
) -> str:
    """Retrieve authentication token from environment variables or .netrc file.

    Args:
        common_names: Common names to use for both env vars and netrc hosts.
                     Can be a string or list of strings. If provided, these names
                     will be added to both environment variables and netrc hosts lists.
        env_names: Environment variable names to check. Can be a string or list of strings.
                  Will be combined with common_names if both are provided.
        netrc_names: Netrc host names to check. Can be a string or list of strings.
                    Will be combined with common_names if both are provided.

    Returns:
        The token value found in environment variables or .netrc file.

    Raises:
        ValueError: If no token is found in any of the specified locations.

    Examples:
        # Use common names for both env vars and netrc hosts
        token = get_token(common_names="GITHUB_TOKEN")

        # Use different names for env vars and netrc hosts
        token = get_token(
            env_names=["ZUUL_TOKEN", "ZUUL_AUTH_TOKEN"],
            netrc_names=["zuul.cc.bmwgroup.net", "zuul.example.com"]
        )

        # Combine common names with additional specific names
        token = get_token(
            common_names="GITHUB_TOKEN",
            netrc_names=["cc-github.bmwgroup.net", "github.com"]
        )
    """

    # Normalize inputs to lists
    def _normalize_to_list(value: list[str] | str | None) -> list[str]:
        if value is None:
            return []
        if isinstance(value, str):
            return [value]
        return value

    common_list = _normalize_to_list(common_names)
    env_list = _normalize_to_list(env_names)
    netrc_list = _normalize_to_list(netrc_names)

    # Combine common names with specific lists
    if common_list:
        env_list.extend(common_list)
        netrc_list.extend(common_list)

    # Try environment variables first
    for env_name in env_list:
        token = os.getenv(env_name)
        if token:
            return token

    # Try .netrc file if no env var found
    if netrc_list:
        try:
            netrc_data = netrc()
            for host in netrc_list:
                host_info = netrc_data.hosts.get(host)
                if host_info:
                    # netrc returns tuple: (login, account, password)
                    # password is typically at index 2
                    token = host_info[2]
                    if token:
                        return token
        except FileNotFoundError:
            # If .netrc file doesn't exist, continue to error message
            pass
        except PermissionError as e:
            raise PermissionError(f"Cannot read .netrc file due to permission error: {e}") from e
        except Exception as e:
            # Re-raise other exceptions (e.g., parsing errors) with context
            raise type(e)(f"Error reading .netrc file: {e}") from e

    # Build error message with all attempted locations
    error_parts: list[str] = []
    if env_list:
        error_parts.append(f"environment variables: {env_list}")
    if netrc_list:
        error_parts.append(f".netrc hosts: {netrc_list}")

    error_message = "No token found"
    if error_parts:
        error_message += f" in {' or '.join(error_parts)}"

    raise ValueError(error_message)
