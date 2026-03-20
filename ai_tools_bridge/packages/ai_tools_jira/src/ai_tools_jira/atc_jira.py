from .instance import BaseBmwJira


class ATCJira(BaseBmwJira):
    """ATC Jira instance using the standard Jira API (/jira endpoint)."""

    def __init__(
        self,
        token_auth: str,
    ):
        super().__init__(
            host="atc.bmwgroup.net/jira",
            token=token_auth,
        )


class ATCServiceDeskJira(BaseBmwJira):
    """ATC Service Desk instance using the Service Desk API (/sd endpoint)."""

    def __init__(
        self,
        token_auth: str,
    ):
        super().__init__(
            host="atc.bmwgroup.net/sd",
            token=token_auth,
        )
