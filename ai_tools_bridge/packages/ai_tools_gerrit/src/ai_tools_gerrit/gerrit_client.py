"""Gerrit REST API client using HTTP Basic Auth and requests."""

import json
from typing import Any
from urllib.parse import quote

import requests


def encode_project_name(name: str) -> str:
    """URL-encode a name for use in Gerrit REST API paths.

    Encodes slashes and other special characters that appear in
    Gerrit project names and file paths.

    Args:
        name: The name to encode (e.g. ``my/project``).

    Returns:
        URL-encoded string (e.g. ``my%2Fproject``).
    """
    return quote(name, safe="")


class GerritApiError(Exception):
    """Raised when a Gerrit API call fails."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class GerritClient:
    """Gerrit REST API client.

    Authenticates via HTTP Basic Auth (username + HTTP password/token).
    Strips the XSSI protection prefix ``)]}'`` from responses before parsing JSON.

    Args:
        base_url: Base URL of the Gerrit instance (e.g. ``https://review.example.com``).
        username: Gerrit account username.
        token: Gerrit HTTP password (generated under Settings → HTTP credentials).
    """

    def __init__(self, base_url: str, username: str, token: str, verify_ssl: bool = True) -> None:
        self._base_url = base_url.rstrip("/")
        self._session = requests.Session()
        self._session.auth = (username, token)
        self._session.headers["Accept"] = "application/json"
        self._session.verify = verify_ssl

    def _parse(self, text: str) -> Any:
        """Strip Gerrit's XSSI prefix and parse JSON."""
        if text.startswith(")]}'"):
            text = text[4:]
        return json.loads(text)

    def get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        """Send an authenticated GET request and return parsed JSON.

        Args:
            path: URL path (e.g. ``/changes/``).
            params: Optional query parameters.

        Returns:
            Parsed JSON response.

        Raises:
            GerritApiError: If the request fails.
        """
        resp = self._session.get(f"{self._base_url}{path}", params=params)
        if not resp.ok:
            raise GerritApiError(
                f"GET {path} failed with status {resp.status_code}: {resp.text[:200]}",
                status_code=resp.status_code,
            )
        return self._parse(resp.text)

    def get_raw(self, path: str, params: dict[str, Any] | None = None) -> str:
        """Send an authenticated GET request and return raw text (not JSON-parsed).

        Useful for endpoints that return non-JSON content such as
        base64-encoded file content.

        Args:
            path: URL path.
            params: Optional query parameters.

        Returns:
            Raw response text with XSSI prefix stripped.

        Raises:
            GerritApiError: If the request fails.
        """
        resp = self._session.get(f"{self._base_url}{path}", params=params)
        if not resp.ok:
            raise GerritApiError(
                f"GET {path} failed with status {resp.status_code}: {resp.text[:200]}",
                status_code=resp.status_code,
            )
        text = resp.text
        if text.startswith(")]}'"):
            text = text[4:]
        return text.lstrip("\n")

    def post(self, path: str, payload: dict[str, Any] | None = None) -> Any:
        """Send an authenticated POST request and return parsed JSON (or None for empty body).

        Args:
            path: URL path.
            payload: Optional JSON payload.

        Returns:
            Parsed JSON response, or ``None`` if the response body is empty.

        Raises:
            GerritApiError: If the request fails.
        """
        resp = self._session.post(f"{self._base_url}{path}", json=payload)
        if not resp.ok:
            raise GerritApiError(
                f"POST {path} failed with status {resp.status_code}: {resp.text[:200]}",
                status_code=resp.status_code,
            )
        text = resp.text.strip()
        if not text:
            return None
        return self._parse(text)

    def put(self, path: str, payload: dict[str, Any] | None = None) -> Any:
        """Send an authenticated PUT request and return parsed JSON (or None for empty body).

        Args:
            path: URL path.
            payload: Optional JSON payload.

        Returns:
            Parsed JSON response, or ``None`` if the response body is empty.

        Raises:
            GerritApiError: If the request fails.
        """
        resp = self._session.put(f"{self._base_url}{path}", json=payload)
        if not resp.ok:
            raise GerritApiError(
                f"PUT {path} failed with status {resp.status_code}: {resp.text[:200]}",
                status_code=resp.status_code,
            )
        text = resp.text.strip()
        if not text:
            return None
        return self._parse(text)
