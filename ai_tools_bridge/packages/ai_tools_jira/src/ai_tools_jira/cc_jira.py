from jira import JIRA

from .instance import BaseBmwJira


class CodeCraftJira(BaseBmwJira):
    def __init__(
        self,
        token_auth: str,
    ):
        super().__init__(
            host="jira.cc.bmwgroup.net",
            token=token_auth,
        )


def get_cc_jira_instance(token: str) -> JIRA:
    return CodeCraftJira(token_auth=token)
