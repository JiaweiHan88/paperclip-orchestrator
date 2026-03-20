from atlassian import Confluence
from requests import Session


class CodeCraftConfluence(Confluence):
    """Confluence API wrapper for BMW CodeCraft team."""

    def __init__(self, token: str):
        """Initialize CodeCraft Confluence connection.

        Args:
            token: Personal Access Token for authentication
        """
        session = Session()
        session.trust_env = False
        super().__init__(  # pyright: ignore
            url="https://confluence.cc.bmwgroup.net",
            token=token,
            cloud=False,  # BMW uses server/data center version
            session=session,
        )


class ATCConfluence(Confluence):
    def __init__(self, token: str):
        """Initialize ATC Confluence connection.

        Args:
            token: Personal Access Token for authentication
        """
        session = Session()
        session.trust_env = False
        super().__init__(  # pyright: ignore
            url="https://atc.bmwgroup.net/confluence",
            token=token,
            cloud=False,
            session=session,
        )


def get_cc_confluence(token: str) -> CodeCraftConfluence:
    """Get an instance of CodeCraftConfluence.

    Args:
        token: Personal Access Token for authentication

    Returns:
        Instance of CodeCraftConfluence
    """
    return CodeCraftConfluence(token=token)


def get_atc_confluence(token: str) -> ATCConfluence:
    """Get an instance of ATCConfluence.

    Args:
        token: Personal Access Token for authentication

    Returns:
        Instance of ATCConfluence
    """
    return ATCConfluence(token=token)
