import json
from json import JSONDecodeError
from pathlib import Path
from typing import Any

from humps.camel import case
from jinja2 import Environment, FileSystemLoader
from loguru import logger
from pydantic import BaseModel, Field, model_validator

from .instance import get_cc_github_instance

HEADERS = {"Accept": "application/vnd.github.text-match+json"}


class SearchResultBase(BaseModel):
    """Root Code Search Result Class"""

    model_config = {
        "alias_generator": case,
        "validate_by_name": True,
        "populate_by_name": True,
        "extra": "ignore",
    }

    @model_validator(mode="before")
    @classmethod
    def extract_text_matches(cls, data: dict[str, Any]) -> dict[str, Any]:
        if not data.get("fragments"):
            text_matches: list[dict[str, Any]] | None = data.get("text_matches")
            if isinstance(text_matches, list):
                fragments: list[str | None] = [match.get("fragment") for match in text_matches if match.get("fragment")]
                if fragments:
                    data["fragments"] = fragments
        return data


class GitHubSearchItem(SearchResultBase):
    """Representation of a single item returned from a GitHub code search.

    Attributes:
        name (str): Name of the matched file in the repository.
        path (str): Path to the matched file in the repository.
        fragments (list[str]): Matched text fragments within the matched file.

    """

    name: str | None = None
    path: str | None = None
    fragments: list[str] = Field(default_factory=list)


class GitHubSearchResponse(SearchResultBase):
    """Representation of the full response from a GitHub code search.

    Attributes:
        total_count (int): Number of files containing the keyword.
        items (list[GitHubSearchItem]): List of individual search result items.

    """

    total_count: int
    incomplete_results: bool
    items: list[GitHubSearchItem] = Field(default_factory=list[GitHubSearchItem])


class CodeSearchResult(SearchResultBase):
    """Representation of a keyword match in a GitHub file.

    Attributes:
        keyword (str): The searched keyword.
        file_name (str): Name of the matched file in the repository.
        file_path (str): Path to the matched file in the repository.
        fragments (list[str]): Matched text fragments within the matched file.

    """

    keyword: str
    file_name: str | None = None
    file_path: str | None = None
    fragments: list[str] | None = Field(default_factory=list)


class GitHubSearchInput(BaseModel):
    """Input model for keyword-searching a github repository."""

    owner: str = Field(
        description="The owner of the repository.",
        examples=["swh", "software-factory"],
    )
    repo: str = Field(
        description="The name of the repository.",
        examples=["repo1", "xpad-shared"],
    )
    keyword: str = Field(
        description="The keyword to search for in the repository.",
        examples=["bug", "refactor", "TODO", "deprecated"],
    )


class GitHubSearch:
    """
    Tool for doing a keyword-search within a GitHub repository
    using the GitHub REST API.

    This class initializes a GitHub API client and constructs a search
    query to find occurrences of a specified keyword within the contents
    of the given repository.
    It retrieves, parses, and formats search results.

    """

    def __init__(self, github_token: str, owner: str, repo: str, keyword: str):
        logger.info(f"Initializing the tool {self.__class__.__name__}.")

        self.github_token = github_token
        self.owner = owner
        self.repo = repo
        self.keyword = keyword
        self.query_params = {"q": f"{keyword} repo:{self.owner}/{self.repo}"}

        # Initialize the Github instance
        self.github = get_cc_github_instance(self.github_token)

    def get_search_data(self) -> str:
        """
        Run the tool. Retrieve and process GitHub search results
        for a specified keyword.

        This method sends a request to the GitHub REST API using
        a predefined query, parses the JSON response, and converts
        the relevant search results into structured 'CodeSearchResult'
        objects.
        The results are then formatted into a Markdown string.

        Returns:
            str: A Markdown-formatted string containing the search results.

        """
        logger.info(f"Sending GitHub search request for keyword='{self.keyword}' in repo='{self.owner}/{self.repo}'.")
        response = self.github.v3_get(
            url_part="/search/code",
            update_headers=HEADERS,
            params=self.query_params,
        )
        try:
            response = json.loads(response)
        except JSONDecodeError:
            logger.exception("Failed to decode JSON")
            raise

        items = response.get("items")
        if not items:
            logger.info(
                f"No search results found using the keyword '{self.keyword}' in repository '{self.owner}/{self.repo}'."
            )
            return ""
        logger.info(f"Found {len(items)} files containing the keyword.")

        logger.info("Parsing response into GitHubSearchResponse object.")
        search_response = GitHubSearchResponse(**response)

        logger.info("Creating CodeSearchResult objects.")
        search_results = [self._create_code_search_result(item) for item in search_response.items]

        md_output = self._to_markdown(search_results)
        return md_output

    def _create_code_search_result(self, item: GitHubSearchItem) -> CodeSearchResult:
        """
        Construct a 'CodeSearchResult' object from a GitHub search result item.

        This method extracts relevant information from a dictionary representing
        a single search result item returned by the GitHub API.

        Args:
            item (GitHubSearchItem): A GitHubSearchItem object containing metadata
                and text match information for a file in the GitHub repository.

        Returns:
            CodeSearchResult: An object containing structured information about the
                keyword match, including file name, file path, and match fragments.

        """
        return CodeSearchResult(
            keyword=self.keyword,
            file_name=item.name,
            file_path=item.path,
            fragments=item.fragments,
        )

    def _to_markdown(self, search_results: list[CodeSearchResult]) -> str:
        """
        Render the list of CodeSearchResult objects into markdown using
        a jinja2 markdown template.

        Args:
            search_results (list[CodeSearchResult]): A list of CodeSearchResult
                objects.

        Returns:
            md_output (str): The markdown output string.

        """
        logger.info("Rendering data to markdown.")
        template_dir = Path(__file__).resolve().parent / "templates"
        env = Environment(loader=FileSystemLoader(template_dir))
        template = env.get_template("template_github_search.md.j2")
        md_output = template.render(
            search_results=search_results,
            keyword=self.keyword,
            owner=self.owner,
            repo=self.repo,
        )
        return md_output
