from ai_tools_base import get_token
from jira import JIRA


class BaseBmwJira(JIRA):
    def __init__(
        self,
        host: str,
        token: str | None = None,
    ):
        options = {
            "cookies": {"SMCHALLENGE": "YES"},
            "headers": {"Accept": "application/json", "Content-Type": "application/json"},
        }

        self.host = f"https://{host}"

        if not token:
            token = get_token(host)

        super().__init__(
            server=self.host,
            token_auth=token,
            options=options,
        )
