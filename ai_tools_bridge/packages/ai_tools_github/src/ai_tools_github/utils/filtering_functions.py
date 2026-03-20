import re

AUTHOR_FILTERS = [
    r"^github-actions$",
    r"^dependabot",
]

CONTENT_FILTERS = [
    r"thank you for your contribution",
    r"auto-merged",
    r"this issue has been automatically closed",
]


def is_author_unwanted(author: str) -> bool:
    """
    Check if the comment is from a certain author.

    Args:
        author: The author of the comment

    Returns:
        is_unwanted_author: True if the content should be excluded, False otherwise

    """

    # Check author filters
    for pattern in AUTHOR_FILTERS:
        if re.search(pattern, author, re.IGNORECASE):
            return True

    return False


def is_content_unwanted(body: str) -> bool:
    """
    Check if the body of the comment contains unwanted content.

    Args:
        body: Body of the comment

    Returns:
        is_unwanted_content: True if the content should be excluded, False otherwise

    """

    # Check content filters
    for pattern in CONTENT_FILTERS:
        if re.search(pattern, body, re.IGNORECASE):
            return True

    return False


def is_author_login_bot(author: str) -> bool:
    """
    Check if the author is a bot

    Args:
        author: The author of the comment

    Returns:
        is_bot: True if the author login is a bot, False otherwise

    """

    return bool(
        author
        in [
            "xpadtech",
            "zuul",
            "etba-app",
            "dependency-graph",
            "putzerfisch",
            "stale",
        ]
    )


def login_startswith_tu(author: str) -> bool:
    """
    Check if the author is a tu bot

    Args:
        author: The author of the comment

    Returns:
        is_tu: True if the author login is a tu bot, False otherwise

    """

    return bool(author.startswith("tu-"))


def is_retrigger_comment(body: str) -> bool:
    """
    Check if the comment is a retrigger comment

    Args:
        body: The body of the comment

    Returns:
        is_retrigger: True if the comment is a retrigger comment, False otherwise

    """

    return not bool(re.search(r"\s", body.strip())) and bool(re.search(r"\w*\-*(re)\-*\w+", body))
