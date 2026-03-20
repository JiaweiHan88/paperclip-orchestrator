"""
Unit tests for the issues_board module.

This test module validates:
1. ProjectBoardIssuesInput and filter dict model validation
2. get_issues_from_project_board function with various scenarios and filters
3. URL parsing for organization and user projects
4. Error handling for invalid URLs
5. GraphQL query execution with different filter combinations
6. _build_search_query helper function
7. get_project_fields function for retrieving project board fields
8. _parse_project_url helper function
"""

from unittest.mock import Mock
from unittest import TestCase

from ai_tools_github.github_client import Github

from ai_tools_github.issues_board import (
    FilteredProjectBoardIssuesInput,
    IssueFilters,
    ProjectBoardIssuesInput,
    ProjectFieldsInput,
    _build_search_query,
    _parse_project_url,
    get_issues_from_project_board,
    get_project_fields,
)


class TestOpenIssuesModels(TestCase):
    """Test the Pydantic models for open issues."""

    def test_project_board_issues_input_org(self):
        """Test ProjectBoardIssuesInput with organization project URL."""
        input_data = ProjectBoardIssuesInput(project_url="https://github.com/orgs/myorg/projects/1")

        self.assertEqual(input_data.project_url, "https://github.com/orgs/myorg/projects/1")

    def test_project_board_issues_input_user(self):
        """Test ProjectBoardIssuesInput with user project URL."""
        input_data = ProjectBoardIssuesInput(project_url="https://github.com/users/myuser/projects/2")

        self.assertEqual(input_data.project_url, "https://github.com/users/myuser/projects/2")


class TestIssueFilters(TestCase):
    """Test the IssueFilters dict type alias."""

    def test_issue_filters_is_dict(self):
        """Test IssueFilters is a dict type alias."""
        filters: IssueFilters = {}
        self.assertIsInstance(filters, dict)

    def test_issue_filters_with_status(self):
        """Test filters dict with different status values."""
        filters_open: IssueFilters = {"status": "open"}
        filters_closed: IssueFilters = {"status": "closed"}
        filters_draft: IssueFilters = {"status": "draft"}
        filters_all: IssueFilters = {"status": "all"}

        self.assertEqual(filters_open["status"], "open")
        self.assertEqual(filters_closed["status"], "closed")
        self.assertEqual(filters_draft["status"], "draft")
        self.assertEqual(filters_all["status"], "all")

    def test_issue_filters_with_all_options(self):
        """Test filters dict with all common options set."""
        filters: IssueFilters = {
            "status": "closed",
            "assignee": "testuser",
            "labels": ["bug", "priority"],
            "milestone": "v1.0",
            "author": "author_user",
            "mentioned": "mentioned_user",
        }

        self.assertEqual(filters["status"], "closed")
        self.assertEqual(filters["assignee"], "testuser")
        self.assertEqual(filters["labels"], ["bug", "priority"])
        self.assertEqual(filters["milestone"], "v1.0")
        self.assertEqual(filters["author"], "author_user")
        self.assertEqual(filters["mentioned"], "mentioned_user")

    def test_project_board_issues_input_with_filters(self):
        """Test FilteredProjectBoardIssuesInput with filters."""
        filters: IssueFilters = {"status": "closed", "assignee": "testuser"}
        input_data = FilteredProjectBoardIssuesInput(
            project_url="https://github.com/orgs/myorg/projects/1",
            filters=filters,
        )

        self.assertEqual(input_data.filters["status"], "closed")
        self.assertEqual(input_data.filters["assignee"], "testuser")


class TestBuildSearchQuery(TestCase):
    """Test the _build_search_query helper function."""

    def test_build_query_empty_filters(self):
        """Test query building with empty filters."""
        filters: IssueFilters = {}
        query = _build_search_query("myorg", 1, filters)

        self.assertIn("is:issue", query)
        self.assertIn("project:myorg/1", query)
        self.assertNotIn("is:open", query)
        self.assertNotIn("is:closed", query)

    def test_build_query_open_status(self):
        """Test query building with open status."""
        filters: IssueFilters = {"status": "open"}
        query = _build_search_query("myorg", 1, filters)

        self.assertIn("is:open", query)
        self.assertNotIn("is:closed", query)

    def test_build_query_closed_status(self):
        """Test query building with closed status."""
        filters: IssueFilters = {"status": "closed"}
        query = _build_search_query("myorg", 1, filters)

        self.assertIn("is:closed", query)
        self.assertNotIn("is:open", query)

    def test_build_query_draft_status(self):
        """Test query building with draft status."""
        filters: IssueFilters = {"status": "draft"}
        query = _build_search_query("myorg", 1, filters)

        self.assertIn("draft:true", query)

    def test_build_query_all_status(self):
        """Test query building with all status (no status filter)."""
        filters: IssueFilters = {"status": "all"}
        query = _build_search_query("myorg", 1, filters)

        self.assertNotIn("is:open", query)
        self.assertNotIn("is:closed", query)
        self.assertNotIn("draft:", query)

    def test_build_query_with_assignee(self):
        """Test query building with assignee filter."""
        filters: IssueFilters = {"assignee": "testuser"}
        query = _build_search_query("myorg", 1, filters)

        self.assertIn("assignee:testuser", query)

    def test_build_query_with_no_assignee(self):
        """Test query building with assignee=none filter."""
        filters: IssueFilters = {"assignee": "none"}
        query = _build_search_query("myorg", 1, filters)

        self.assertIn("no:assignee", query)
        self.assertNotIn("assignee:none", query)

    def test_build_query_with_labels(self):
        """Test query building with label filters."""
        filters: IssueFilters = {"labels": ["bug", "high-priority"]}
        query = _build_search_query("myorg", 1, filters)

        self.assertIn("label:bug", query)
        self.assertIn("label:high-priority", query)

    def test_build_query_with_single_label_as_string(self):
        """Test query building with single label as string."""
        filters: IssueFilters = {"labels": "bug"}
        query = _build_search_query("myorg", 1, filters)

        self.assertIn("label:bug", query)

    def test_build_query_with_label_containing_space(self):
        """Test query building with label containing space."""
        filters: IssueFilters = {"labels": ["in progress", "bug"]}
        query = _build_search_query("myorg", 1, filters)

        self.assertIn('label:"in progress"', query)
        self.assertIn("label:bug", query)

    def test_build_query_with_no_label(self):
        """Test query building with labels=none filter."""
        filters: IssueFilters = {"labels": "none"}
        query = _build_search_query("myorg", 1, filters)

        self.assertIn("no:label", query)

    def test_build_query_with_milestone(self):
        """Test query building with milestone filter."""
        filters: IssueFilters = {"milestone": "v1.0"}
        query = _build_search_query("myorg", 1, filters)

        self.assertIn("milestone:v1.0", query)

    def test_build_query_with_milestone_containing_space(self):
        """Test query building with milestone containing space."""
        filters: IssueFilters = {"milestone": "Sprint 1"}
        query = _build_search_query("myorg", 1, filters)

        self.assertIn('milestone:"Sprint 1"', query)

    def test_build_query_with_no_milestone(self):
        """Test query building with milestone=none filter."""
        filters: IssueFilters = {"milestone": "none"}
        query = _build_search_query("myorg", 1, filters)

        self.assertIn("no:milestone", query)

    def test_build_query_with_author(self):
        """Test query building with author filter."""
        filters: IssueFilters = {"author": "author_user"}
        query = _build_search_query("myorg", 1, filters)

        self.assertIn("author:author_user", query)

    def test_build_query_with_mentioned(self):
        """Test query building with mentioned filter."""
        filters: IssueFilters = {"mentioned": "mentioned_user"}
        query = _build_search_query("myorg", 1, filters)

        self.assertIn("mentions:mentioned_user", query)

    def test_build_query_complex_filters(self):
        """Test query building with multiple filters combined."""
        filters: IssueFilters = {
            "status": "open",
            "assignee": "dev_user",
            "labels": ["bug"],
            "author": "reporter",
        }
        query = _build_search_query("myorg", 5, filters)

        self.assertIn("is:issue", query)
        self.assertIn("project:myorg/5", query)
        self.assertIn("is:open", query)
        self.assertIn("assignee:dev_user", query)
        self.assertIn("label:bug", query)
        self.assertIn("author:reporter", query)

    def test_build_query_case_insensitive_keys(self):
        """Test that filter keys are case-insensitive."""
        filters: IssueFilters = {"Status": "open", "ASSIGNEE": "user"}
        query = _build_search_query("myorg", 1, filters)

        self.assertIn("is:open", query)
        self.assertIn("assignee:user", query)


class TestGetIssuesFromProjectBoard(TestCase):
    """Test the get_issues_from_project_board function."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_github = Mock(spec=Github)

    def _create_mock_response(self, issues_data):
        """Helper to create mock GraphQL response with issue data."""
        nodes = []
        for issue in issues_data:
            nodes.append(
                {
                    "title": issue.get("title", ""),
                    "body": issue.get("body", ""),
                    "url": issue.get("url", ""),
                    "number": issue.get("number", 1),
                    "state": issue.get("state", "OPEN"),
                    "assignees": {"nodes": [{"login": a} for a in issue.get("assignees", [])]},
                    "labels": {"nodes": [{"name": lbl} for lbl in issue.get("labels", [])]},
                }
            )
        return {
            "search": {
                "issueCount": len(nodes),
                "pageInfo": {"endCursor": None, "hasNextPage": False},
                "nodes": nodes,
            }
        }

    def test_get_issues_default_filters(self):
        """Test retrieval with no filters."""
        self.mock_github.query.return_value = self._create_mock_response(
            [
                {"title": "Issue 1", "body": "Body 1", "url": "https://github.com/o/r/issues/1"},
            ]
        )

        result = get_issues_from_project_board(
            project_url="https://github.com/orgs/myorg/projects/1",
            github=self.mock_github,
        )

        self.assertEqual(len(result), 1)
        call_args = self.mock_github.query.call_args[0][0]
        self.assertIn("is:issue", call_args)
        self.assertIn("project:myorg/1", call_args)

    def test_get_issues_open_status(self):
        """Test retrieval with open status filter."""
        self.mock_github.query.return_value = self._create_mock_response(
            [
                {"title": "Open Issue", "state": "OPEN"},
            ]
        )

        result = get_issues_from_project_board(
            project_url="https://github.com/orgs/myorg/projects/1",
            github=self.mock_github,
            filters={"status": "open"},
        )

        call_args = self.mock_github.query.call_args[0][0]
        self.assertIn("is:open", call_args)

    def test_get_issues_closed_status(self):
        """Test retrieval with closed status filter."""
        self.mock_github.query.return_value = self._create_mock_response(
            [
                {"title": "Closed Issue", "state": "CLOSED"},
            ]
        )

        result = get_issues_from_project_board(
            project_url="https://github.com/orgs/myorg/projects/1",
            github=self.mock_github,
            filters={"status": "closed"},
        )

        call_args = self.mock_github.query.call_args[0][0]
        self.assertIn("is:closed", call_args)
        self.assertNotIn("is:open", call_args)

    def test_get_issues_all_status(self):
        """Test retrieval with all status filter (no status restriction)."""
        self.mock_github.query.return_value = self._create_mock_response([])

        get_issues_from_project_board(
            project_url="https://github.com/orgs/myorg/projects/1",
            github=self.mock_github,
            filters={"status": "all"},
        )

        call_args = self.mock_github.query.call_args[0][0]
        self.assertNotIn("is:open", call_args)
        self.assertNotIn("is:closed", call_args)

    def test_get_issues_with_assignee_filter(self):
        """Test retrieval with assignee filter."""
        self.mock_github.query.return_value = self._create_mock_response(
            [
                {"title": "Issue", "assignees": ["testuser"]},
            ]
        )

        get_issues_from_project_board(
            project_url="https://github.com/orgs/myorg/projects/1",
            github=self.mock_github,
            filters={"assignee": "testuser"},
        )

        call_args = self.mock_github.query.call_args[0][0]
        self.assertIn("assignee:testuser", call_args)

    def test_get_issues_with_labels_filter(self):
        """Test retrieval with labels filter."""
        self.mock_github.query.return_value = self._create_mock_response(
            [
                {"title": "Bug", "labels": ["bug", "critical"]},
            ]
        )

        get_issues_from_project_board(
            project_url="https://github.com/orgs/myorg/projects/1",
            github=self.mock_github,
            filters={"labels": ["bug", "critical"]},
        )

        call_args = self.mock_github.query.call_args[0][0]
        self.assertIn("label:bug", call_args)
        self.assertIn("label:critical", call_args)

    def test_get_issues_response_includes_state_assignees_labels(self):
        """Test that response includes state, assignees, and labels."""
        self.mock_github.query.return_value = self._create_mock_response(
            [
                {
                    "title": "Test Issue",
                    "body": "Body",
                    "url": "https://github.com/o/r/issues/1",
                    "state": "OPEN",
                    "assignees": ["user1", "user2"],
                    "labels": ["bug", "enhancement"],
                },
            ]
        )

        result = get_issues_from_project_board(
            project_url="https://github.com/orgs/myorg/projects/1",
            github=self.mock_github,
        )

        issue = result[0]
        self.assertEqual(issue["state"], "open")
        self.assertEqual(issue["assignees"], ["user1", "user2"])
        self.assertEqual(issue["labels"], ["bug", "enhancement"])


class TestParseProjectUrl(TestCase):
    """Test the _parse_project_url helper function."""

    def test_parse_org_project_url(self):
        """Test parsing organization project URL."""
        owner_type, owner_name, project_number = _parse_project_url("https://github.com/orgs/myorg/projects/5")

        self.assertEqual(owner_type, "organization")
        self.assertEqual(owner_name, "myorg")
        self.assertEqual(project_number, 5)

    def test_parse_user_project_url(self):
        """Test parsing user project URL."""
        owner_type, owner_name, project_number = _parse_project_url("https://github.com/users/myuser/projects/3")

        self.assertEqual(owner_type, "user")
        self.assertEqual(owner_name, "myuser")
        self.assertEqual(project_number, 3)

    def test_parse_url_with_trailing_slash(self):
        """Test parsing URL with trailing slash."""
        owner_type, owner_name, project_number = _parse_project_url("https://github.com/orgs/myorg/projects/1/")

        self.assertEqual(owner_type, "organization")
        self.assertEqual(owner_name, "myorg")
        self.assertEqual(project_number, 1)

    def test_parse_invalid_url_format(self):
        """Test error handling for invalid URL format."""
        with self.assertRaises(ValueError) as context:
            _parse_project_url("https://github.com/invalid")

        self.assertIn("Invalid project URL format", str(context.exception))

    def test_parse_unsupported_path_type(self):
        """Test error handling for unsupported path type."""
        with self.assertRaises(ValueError) as context:
            _parse_project_url("https://github.com/repos/owner/projects/1")

        self.assertIn("Unsupported project URL format", str(context.exception))

    def test_parse_not_projects_url(self):
        """Test error handling for URL not pointing to projects."""
        with self.assertRaises(ValueError) as context:
            _parse_project_url("https://github.com/orgs/myorg/repositories/1")

        self.assertIn("URL does not point to a projects board", str(context.exception))

    def test_parse_invalid_project_number(self):
        """Test error handling for invalid project number."""
        with self.assertRaises(ValueError) as context:
            _parse_project_url("https://github.com/orgs/myorg/projects/abc")

        self.assertIn("Invalid project number in URL", str(context.exception))


class TestProjectFieldsInputModel(TestCase):
    """Test the ProjectFieldsInput model."""

    def test_project_fields_input(self):
        """Test ProjectFieldsInput model."""
        input_data = ProjectFieldsInput(project_url="https://github.com/orgs/myorg/projects/1")

        self.assertEqual(input_data.project_url, "https://github.com/orgs/myorg/projects/1")


class TestGetProjectFields(TestCase):
    """Test the get_project_fields function."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_github = Mock(spec=Github)

    def test_get_project_fields_org_success(self):
        """Test successful retrieval of fields from organization project."""
        mock_response = {
            "organization": {
                "projectV2": {
                    "id": "PVT_kwDOA123",
                    "title": "Development Board",
                    "fields": {
                        "nodes": [
                            {"id": "PVTF_1", "name": "Title", "dataType": "TITLE"},
                            {"id": "PVTF_2", "name": "Assignees", "dataType": "ASSIGNEES"},
                            {
                                "id": "PVTF_3",
                                "name": "Status",
                                "dataType": "SINGLE_SELECT",
                                "options": [
                                    {"id": "opt_1", "name": "Todo"},
                                    {"id": "opt_2", "name": "In Progress"},
                                    {"id": "opt_3", "name": "Done"},
                                ],
                            },
                            {
                                "id": "PVTF_4",
                                "name": "Priority",
                                "dataType": "SINGLE_SELECT",
                                "options": [
                                    {"id": "opt_h", "name": "High"},
                                    {"id": "opt_m", "name": "Medium"},
                                    {"id": "opt_l", "name": "Low"},
                                ],
                            },
                        ]
                    },
                }
            }
        }
        self.mock_github.query.return_value = mock_response

        result = get_project_fields(
            project_url="https://github.com/orgs/myorg/projects/1",
            github=self.mock_github,
        )

        self.assertEqual(result["project_id"], "PVT_kwDOA123")
        self.assertEqual(result["project_title"], "Development Board")
        self.assertEqual(len(result["fields"]), 4)

        # Check Status field
        status_field = next(f for f in result["fields"] if f["name"] == "Status")
        self.assertEqual(status_field["field_type"], "SINGLE_SELECT")
        self.assertEqual(len(status_field["options"]), 3)
        self.assertEqual(status_field["options"][0], "Todo")

    def test_get_project_fields_user_success(self):
        """Test successful retrieval of fields from user project."""
        mock_response = {
            "user": {
                "projectV2": {
                    "id": "PVT_user123",
                    "title": "Personal Tasks",
                    "fields": {
                        "nodes": [
                            {"id": "PVTF_1", "name": "Title", "dataType": "TITLE"},
                        ]
                    },
                }
            }
        }
        self.mock_github.query.return_value = mock_response

        result = get_project_fields(
            project_url="https://github.com/users/myuser/projects/2",
            github=self.mock_github,
        )

        self.assertEqual(result["project_id"], "PVT_user123")
        self.assertEqual(result["project_title"], "Personal Tasks")
        self.assertEqual(len(result["fields"]), 1)

    def test_get_project_fields_with_iteration(self):
        """Test retrieval of fields including iteration field."""
        mock_response = {
            "organization": {
                "projectV2": {
                    "id": "PVT_123",
                    "title": "Sprint Board",
                    "fields": {
                        "nodes": [
                            {
                                "id": "PVTF_iter",
                                "name": "Sprint",
                                "dataType": "ITERATION",
                                "configuration": {
                                    "iterations": [
                                        {"id": "iter_1", "title": "Sprint 1"},
                                        {"id": "iter_2", "title": "Sprint 2"},
                                    ]
                                },
                            },
                        ]
                    },
                }
            }
        }
        self.mock_github.query.return_value = mock_response

        result = get_project_fields(
            project_url="https://github.com/orgs/myorg/projects/1",
            github=self.mock_github,
        )

        sprint_field = result["fields"][0]
        self.assertEqual(sprint_field["name"], "Sprint")
        self.assertEqual(sprint_field["field_type"], "ITERATION")
        self.assertEqual(len(sprint_field["options"]), 2)
        self.assertEqual(sprint_field["options"][0], "Sprint 1")
        self.assertEqual(sprint_field["options"][1], "Sprint 2")

    def test_get_project_fields_no_data(self):
        """Test handling when no data is returned."""
        self.mock_github.query.return_value = None

        result = get_project_fields(
            project_url="https://github.com/orgs/myorg/projects/1",
            github=self.mock_github,
        )

        self.assertEqual(result["fields"], [])

    def test_get_project_fields_graphql_errors(self):
        """Test handling of GraphQL errors."""
        mock_response = {
            "errors": [{"message": "Project not found"}],
        }
        self.mock_github.query.return_value = mock_response

        result = get_project_fields(
            project_url="https://github.com/orgs/myorg/projects/1",
            github=self.mock_github,
        )

        self.assertEqual(result["fields"], [])

    def test_get_project_fields_no_project_data(self):
        """Test handling when project data is missing."""
        mock_response = {"organization": {"projectV2": None}}
        self.mock_github.query.return_value = mock_response

        result = get_project_fields(
            project_url="https://github.com/orgs/myorg/projects/1",
            github=self.mock_github,
        )

        self.assertEqual(result["fields"], [])

    def test_get_project_fields_invalid_url(self):
        """Test error handling for invalid URL."""
        with self.assertRaises(Exception) as context:
            get_project_fields(
                project_url="https://github.com/invalid",
                github=self.mock_github,
            )

        self.assertIn("Unable to fetch project fields", str(context.exception))

    def test_get_project_fields_query_exception(self):
        """Test handling of exception during GraphQL query."""
        self.mock_github.query.side_effect = Exception("Network error")

        with self.assertRaises(Exception) as context:
            get_project_fields(
                project_url="https://github.com/orgs/myorg/projects/1",
                github=self.mock_github,
            )

        self.assertIn("Unable to fetch project fields", str(context.exception))
        self.assertIn("Network error", str(context.exception))

    def test_get_project_fields_empty_nodes(self):
        """Test handling when field nodes are empty or None."""
        mock_response = {
            "organization": {
                "projectV2": {
                    "id": "PVT_123",
                    "title": "Test",
                    "fields": {"nodes": [None, {"id": "f1", "name": "Title", "dataType": "TEXT"}, None]},
                }
            }
        }
        self.mock_github.query.return_value = mock_response

        result = get_project_fields(
            project_url="https://github.com/orgs/myorg/projects/1",
            github=self.mock_github,
        )

        # Should skip None nodes
        self.assertEqual(len(result["fields"]), 1)
        self.assertEqual(result["fields"][0]["name"], "Title")


if __name__ == "__main__":
    import unittest

    unittest.main()
