from ai_tools_github.github_client import Github


def get_cc_github_instance(token: str) -> Github:
    return Github(
        url="https://cc-github.bmwgroup.net/api/graphql",
        v3_url="https://cc-github.bmwgroup.net/api/v3",
        token=token,
    )


def get_cc_github_app_instance(app_pem: bytes, app_id: int) -> Github:
    return Github(
        url="https://cc-github.bmwgroup.net/api/graphql",
        v3_url="https://cc-github.bmwgroup.net/api/v3",
        app_pem=app_pem,
        app_id=app_id,
    )


def get_atc_github_instance(token: str) -> Github:
    return Github(
        url="https://atc-github.azure.cloud.bmw/api/graphql",
        v3_url="https://atc-github.azure.cloud.bmw/api/v3",
        token=token,
    )
