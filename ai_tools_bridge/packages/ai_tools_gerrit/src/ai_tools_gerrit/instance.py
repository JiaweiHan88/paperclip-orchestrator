"""Factory functions for creating GerritClient instances."""

from ai_tools_gerrit.gerrit_client import GerritClient

CC_GERRIT_URL = "https://gerrit.cc.bmwgroup.net/a"


def get_cc_gerrit_instance(username: str, token: str, verify_ssl: bool = True) -> GerritClient:
    """Create a GerritClient for the CC Gerrit instance.

    Args:
        username: Gerrit account username.
        token: Gerrit HTTP password (generated under Settings → HTTP credentials).
        verify_ssl: Whether to verify SSL certificates (default ``True``).

    Returns:
        Configured GerritClient instance for ``gerrit.cc.bmwgroup.net``.
    """
    return GerritClient(base_url=CC_GERRIT_URL, username=username, token=token, verify_ssl=verify_ssl)
