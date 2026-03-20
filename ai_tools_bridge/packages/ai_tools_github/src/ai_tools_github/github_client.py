"""GitHub API client supporting both GraphQL (v4) and REST (v3) via requests.

Drop-in replacement for gitaudit.github.instance.Github.
"""

from __future__ import annotations

import time
from typing import Any, TypeVar

import requests
from pydantic import BaseModel

from ai_tools_github.github_types import FileDeletion

T = TypeVar("T", bound=BaseModel)


class GithubApiError(Exception):
    """Raised when a GitHub API call fails."""

    def __init__(self, message: str, errors: list[dict[str, Any]] | None = None) -> None:
        super().__init__(message)
        self.errors = errors or []


class _SimpleObject:
    """Simple attribute-access wrapper over a dict, for lightweight GraphQL results."""

    def __init__(self, data: dict[str, Any]) -> None:
        for key, value in data.items():
            snake_key = _camel_to_snake(key)
            setattr(self, snake_key, value)


def _camel_to_snake(name: str) -> str:
    """Convert camelCase to snake_case."""
    result: list[str] = []
    for i, char in enumerate(name):
        if char.isupper() and i > 0:
            result.append("_")
        result.append(char.lower())
    return "".join(result)


class Github:
    """GitHub API client supporting both GraphQL (v4) and REST (v3).

    Args:
        url: GraphQL API endpoint URL.
        v3_url: REST API v3 endpoint URL.
        token: Personal access token for authentication.
        app_pem: GitHub App private key bytes for App authentication.
        app_id: GitHub App ID for App authentication.
    """

    def __init__(
        self,
        url: str = "https://api.github.com/graphql",
        v3_url: str = "https://api.github.com",
        token: str | None = None,
        app_pem: bytes | None = None,
        app_id: int | None = None,
    ) -> None:
        self._graphql_url = url
        self._v3_url = v3_url.rstrip("/")
        self._session = requests.Session()
        self._session.headers["Accept"] = "application/json"

        if token:
            self._session.headers["Authorization"] = f"bearer {token}"
        elif app_pem is not None and app_id is not None:
            self._setup_app_auth(app_pem, app_id)

    def _setup_app_auth(self, app_pem: bytes, app_id: int) -> None:
        """Set up GitHub App authentication using JWT."""
        try:
            import jwt
        except ImportError as e:
            msg = "PyJWT is required for GitHub App authentication. Install with: pip install PyJWT cryptography"
            raise ImportError(msg) from e

        now = int(time.time())
        payload = {
            "iat": now - 60,
            "exp": now + (10 * 60),
            "iss": app_id,
        }
        jwt_token = jwt.encode(payload, app_pem, algorithm="RS256")

        # Get installation ID
        headers = {"Authorization": f"Bearer {jwt_token}", "Accept": "application/vnd.github+json"}
        resp = self._session.get(f"{self._v3_url}/app/installations", headers=headers)
        resp.raise_for_status()
        installations = resp.json()

        if not installations:
            msg = f"No installations found for GitHub App {app_id}"
            raise GithubApiError(msg)

        installation_id = installations[0]["id"]

        # Get installation access token
        resp = self._session.post(
            f"{self._v3_url}/app/installations/{installation_id}/access_tokens",
            headers=headers,
        )
        resp.raise_for_status()
        access_token = resp.json()["token"]

        self._session.headers["Authorization"] = f"bearer {access_token}"

    # ── GraphQL core ──────────────────────────────────────────────────

    def _graphql(self, query_string: str, variables: dict[str, Any] | None = None) -> dict[str, Any]:
        """Execute a GraphQL request and return the data portion of the response."""
        payload: dict[str, Any] = {"query": query_string}
        if variables:
            payload["variables"] = variables

        resp = self._session.post(self._graphql_url, json=payload)
        resp.raise_for_status()
        result = resp.json()

        if "errors" in result:
            error_messages = "; ".join(e.get("message", str(e)) for e in result["errors"])
            raise GithubApiError(f"GraphQL errors: {error_messages}", result["errors"])

        return result.get("data", result)

    def query(self, graphql_string: str) -> dict[str, Any]:
        """Execute a GraphQL query or mutation.

        If the string starts with 'mutation', it is sent as-is.
        Otherwise, it is wrapped in query { ... }.
        """
        stripped = graphql_string.strip()
        if stripped.startswith("mutation") or stripped.startswith("query") or stripped.startswith("{"):
            return self._graphql(stripped)
        return self._graphql(f"{{ {stripped} }}")

    # ── GraphQL query methods ─────────────────────────────────────────

    def pull_request(
        self,
        owner: str,
        repo: str,
        number: int,
        querydata: str = "id",
        instance_class: type[T] | None = None,
    ) -> Any:
        """Fetch a pull request via GraphQL.

        Args:
            owner: Repository owner.
            repo: Repository name.
            number: Pull request number.
            querydata: GraphQL fields to query.
            instance_class: Optional Pydantic model class to instantiate with the result.

        Returns:
            An instance of instance_class if provided, otherwise a simple attribute-access object.
        """
        gql = (
            f'{{ repository(owner: "{owner}", name: "{repo}") {{ pullRequest(number: {number}) {{ {querydata} }} }} }}'
        )
        data = self._graphql(gql)
        pr_data = data["repository"]["pullRequest"]

        if instance_class is not None:
            return instance_class.model_validate(pr_data)
        return _SimpleObject(pr_data)

    def search_pull_requests(
        self,
        search_query: str,
        querydata: str = "id",
        instance_class: type[T] | None = None,
    ) -> list[Any]:
        """Search for pull requests via GraphQL.

        Args:
            search_query: GitHub search query string.
            querydata: GraphQL fields to query for each result.
            instance_class: Optional Pydantic model class to instantiate results with.

        Returns:
            List of model instances or simple objects.
        """
        gql = (
            f"{{ search(type: ISSUE, first: 100, "
            f'query: "{search_query}") '
            f"{{ nodes {{ ... on PullRequest {{ {querydata} }} }} }} }}"
        )
        data = self._graphql(gql)
        nodes = data["search"]["nodes"]

        if instance_class is not None:
            return [instance_class.model_validate(node) for node in nodes if node]
        return [_SimpleObject(node) for node in nodes if node]

    def get_commit_for_expression(
        self,
        owner: str,
        repo: str,
        expression: str,
        querydata: str = "oid",
    ) -> Any:
        """Get a commit by ref expression (branch name, tag, or SHA).

        Args:
            owner: Repository owner.
            repo: Repository name.
            expression: Git ref expression (e.g., "main", "HEAD", commit SHA).
            querydata: GraphQL fields to query.

        Returns:
            A simple attribute-access object with the queried fields.
        """
        gql = (
            f'{{ repository(owner: "{owner}", name: "{repo}") '
            f'{{ object(expression: "{expression}") '
            f"{{ ... on Commit {{ {querydata} }} }} }} }}"
        )
        data = self._graphql(gql)
        obj_data = data["repository"]["object"]

        if obj_data is None:
            msg = f"Could not resolve expression '{expression}' in {owner}/{repo}"
            raise GithubApiError(msg)

        return _SimpleObject(obj_data)

    def get_file_content(self, owner: str, repo: str, ref: str, file_path: str) -> str:
        """Get file content from a repository via GraphQL.

        Args:
            owner: Repository owner.
            repo: Repository name.
            ref: Git ref (branch, tag, or SHA).
            file_path: Path to the file in the repository.

        Returns:
            The file content as a string.
        """
        expression = f"{ref}:{file_path}"
        gql = (
            f'{{ repository(owner: "{owner}", name: "{repo}") '
            f'{{ object(expression: "{expression}") '
            f"{{ ... on Blob {{ text }} }} }} }}"
        )
        data = self._graphql(gql)
        obj = data["repository"]["object"]

        if obj is None:
            msg = f"File not found: {file_path} at ref {ref} in {owner}/{repo}"
            raise GithubApiError(msg)

        return obj["text"]

    def get_repository(self, owner: str, repo: str, querydata: str = "id") -> Any:
        """Get repository information via GraphQL.

        Args:
            owner: Repository owner.
            repo: Repository name.
            querydata: GraphQL fields to query.

        Returns:
            A simple attribute-access object with the queried fields.
        """
        gql = f'{{ repository(owner: "{owner}", name: "{repo}") {{ {querydata} }} }}'
        data = self._graphql(gql)
        return _SimpleObject(data["repository"])

    def get_label_id(self, owner: str, repo: str, label_name: str) -> str | None:
        """Get the node ID of a label by name.

        Args:
            owner: Repository owner.
            repo: Repository name.
            label_name: Name of the label.

        Returns:
            The label's node ID, or None if not found.
        """
        gql = f'{{ repository(owner: "{owner}", name: "{repo}") {{ label(name: "{label_name}") {{ id }} }} }}'
        data = self._graphql(gql)
        label = data["repository"]["label"]
        if label is None:
            return None
        return label["id"]

    # ── GraphQL mutation methods ──────────────────────────────────────

    def _mutate(self, mutation: str) -> dict[str, Any]:
        """Execute a GraphQL mutation."""
        return self._graphql(f"mutation {{ {mutation} }}")

    def create_branch(self, owner: str, repo: str, base_oid: str, ref_name: str) -> None:
        """Create a new branch.

        Args:
            owner: Repository owner.
            repo: Repository name.
            base_oid: The commit OID to branch from.
            ref_name: The name of the new branch.
        """
        # First get the repository ID
        repo_obj = self.get_repository(owner, repo, "id")
        mutation = (
            f'createRef(input: {{repositoryId: "{repo_obj.id}", '
            f'name: "refs/heads/{ref_name}", oid: "{base_oid}"}}) '
            f"{{ ref {{ name }} }}"
        )
        self._mutate(mutation)

    def create_commit_on_branch(
        self,
        owner: str,
        repo: str,
        ref_name: str,
        head_sha: str,
        message_headline: str,
        message_body: str | None = None,
        additions: list[Any] | None = None,
        deletions: list[FileDeletion] | None = None,
        querydata: str = "oid",
    ) -> Any:
        """Create a commit on a branch.

        Args:
            owner: Repository owner.
            repo: Repository name.
            ref_name: Branch name.
            head_sha: Expected HEAD SHA of the branch.
            message_headline: Commit message headline.
            message_body: Optional commit message body.
            additions: List of FileAddition objects.
            deletions: List of FileDeletion objects.
            querydata: GraphQL fields to return for the created commit.

        Returns:
            A simple object with the queried commit fields, or None.
        """
        additions_gql = ""
        if additions:
            addition_entries = ", ".join(f'{{path: "{a.path}", contents: "{a.contents}"}}' for a in additions)
            additions_gql = f"additions: [{addition_entries}]"

        deletions_gql = ""
        if deletions:
            deletion_entries = ", ".join(f'{{path: "{d.path}"}}' for d in deletions)
            deletions_gql = f"deletions: [{deletion_entries}]"

        file_changes_parts = [p for p in [additions_gql, deletions_gql] if p]
        file_changes = ", ".join(file_changes_parts)

        message_parts = f'headline: "{message_headline}"'
        if message_body:
            escaped_body = message_body.replace('"', '\\"').replace("\n", "\\n")
            message_parts += f', body: "{escaped_body}"'

        nwo = f"{owner}/{repo}"
        mutation = (
            f"createCommitOnBranch(input: {{"
            f'branch: {{repositoryNameWithOwner: "{nwo}", branchName: "{ref_name}"}}, '
            f"message: {{{message_parts}}}, "
            f'expectedHeadOid: "{head_sha}", '
            f"fileChanges: {{{file_changes}}}"
            f"}}) {{ commit {{ {querydata} }} }}"
        )

        data = self._mutate(mutation)
        commit_data = data.get("createCommitOnBranch", {}).get("commit")
        if commit_data:
            return _SimpleObject(commit_data)
        return None

    def create_pull_request(
        self,
        repository_id: str,
        head_ref_name: str,
        base_ref_name: str,
        title: str,
        body: str | None = None,
        draft: bool = False,
        querydata: str = "id number url",
    ) -> Any:
        """Create a new pull request.

        Args:
            repository_id: The node ID of the repository.
            head_ref_name: The head branch name.
            base_ref_name: The base branch name.
            title: The PR title.
            body: The PR body/description.
            draft: Whether to create as a draft PR.
            querydata: GraphQL fields to return.

        Returns:
            A simple object with the queried PR fields, or None.
        """
        escaped_title = title.replace('"', '\\"')
        body_part = ""
        if body:
            escaped_body = body.replace('"', '\\"').replace("\n", "\\n")
            body_part = f', body: "{escaped_body}"'

        draft_part = "true" if draft else "false"

        mutation = (
            f"createPullRequest(input: {{"
            f'repositoryId: "{repository_id}", '
            f'headRefName: "{head_ref_name}", '
            f'baseRefName: "{base_ref_name}", '
            f'title: "{escaped_title}"'
            f"{body_part}, "
            f"draft: {draft_part}"
            f"}}) {{ pullRequest {{ {querydata} }} }}"
        )

        data = self._mutate(mutation)
        pr_data = data.get("createPullRequest", {}).get("pullRequest")
        if pr_data:
            return _SimpleObject(pr_data)
        return None

    def add_comment(self, subject_id: str, body: str) -> str:
        """Add a comment to an issue or pull request.

        Args:
            subject_id: The node ID of the subject (issue or PR).
            body: The comment body text.

        Returns:
            The node ID of the created comment.
        """
        escaped_body = body.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
        mutation = (
            f'addComment(input: {{subjectId: "{subject_id}", '
            f'body: "{escaped_body}"}}) '
            f"{{ commentEdge {{ node {{ id }} }} }}"
        )
        data = self._mutate(mutation)
        return data["addComment"]["commentEdge"]["node"]["id"]

    def get_comment_url(self, node_id: str) -> str:
        """Get the URL of a comment by its node ID.

        Args:
            node_id: The node ID of the comment.

        Returns:
            The URL of the comment.
        """
        gql = f'{{ node(id: "{node_id}") {{ ... on IssueComment {{ url }} }} }}'
        data = self._graphql(gql)
        return data["node"]["url"]

    def create_reaction(self, subject_id: str, content: Any) -> None:
        """Add a reaction to a subject (comment, issue, PR).

        Args:
            subject_id: The node ID of the subject.
            content: The reaction type (e.g., Reaction.THUMBS_UP or string "THUMBS_UP").
        """
        content_str = content.value if hasattr(content, "value") else str(content)
        mutation = (
            f'addReaction(input: {{subjectId: "{subject_id}", content: {content_str}}}) {{ reaction {{ content }} }}'
        )
        self._mutate(mutation)

    def add_label_to_labelable(self, labelable_id: str, label_ids: list[str]) -> None:
        """Add labels to a labelable object (issue or PR).

        Args:
            labelable_id: The node ID of the issue or PR.
            label_ids: List of label node IDs to add.
        """
        ids_str = ", ".join(f'"{lid}"' for lid in label_ids)
        mutation = (
            f'addLabelsToLabelable(input: {{labelableId: "{labelable_id}", '
            f"labelIds: [{ids_str}]}}) "
            f"{{ labelable {{ ... on PullRequest {{ id }} ... on Issue {{ id }} }} }}"
        )
        self._mutate(mutation)

    def remove_label_from_labelable(self, labelable_id: str, label_ids: list[str]) -> None:
        """Remove labels from a labelable object (issue or PR).

        Args:
            labelable_id: The node ID of the issue or PR.
            label_ids: List of label node IDs to remove.
        """
        ids_str = ", ".join(f'"{lid}"' for lid in label_ids)
        mutation = (
            f'removeLabelsFromLabelable(input: {{labelableId: "{labelable_id}", '
            f"labelIds: [{ids_str}]}}) "
            f"{{ labelable {{ ... on PullRequest {{ id }} ... on Issue {{ id }} }} }}"
        )
        self._mutate(mutation)

    def update_pull_request(self, pull_request_id: str, body: str) -> None:
        """Update a pull request's body/description.

        Args:
            pull_request_id: The node ID of the pull request.
            body: The new body text.
        """
        escaped_body = body.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
        mutation = (
            f'updatePullRequest(input: {{pullRequestId: "{pull_request_id}", '
            f'body: "{escaped_body}"}}) '
            f"{{ pullRequest {{ id }} }}"
        )
        self._mutate(mutation)

    # ── REST v3 methods ───────────────────────────────────────────────

    def v3_get(
        self,
        url_part: str,
        update_headers: dict[str, str] | None = None,
        params: dict[str, str] | None = None,
    ) -> str:
        """Make a REST API v3 GET request.

        Args:
            url_part: The URL path (appended to v3_url).
            update_headers: Additional headers to include.
            params: Query parameters.

        Returns:
            The response text.
        """
        headers = dict(self._session.headers)
        if update_headers:
            headers.update(update_headers)

        resp = requests.get(
            f"{self._v3_url}{url_part}",
            headers=headers,
            params=params,
        )
        resp.raise_for_status()
        return resp.text

    def pull_request_diff(self, owner: str, repo: str, number: int) -> str:
        """Get the diff of a pull request via REST API.

        Args:
            owner: Repository owner.
            repo: Repository name.
            number: Pull request number.

        Returns:
            The diff content as a string.
        """
        return self.v3_get(
            f"/repos/{owner}/{repo}/pulls/{number}",
            update_headers={"Accept": "application/vnd.github.v3.diff"},
        )
