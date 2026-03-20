"""Tests for JIRA tools exports."""

from ai_tools_jira.add_comment import AddJiraCommentInput
from ai_tools_jira.attachment import JiraAttachmentDownloadInput
from ai_tools_jira.create_ticket import CreateJiraTicketInput
from ai_tools_jira.fields import GetJiraFieldsInput
from ai_tools_jira.issue import JiraIssueInput
from ai_tools_jira.pull_requests import JiraPullRequestsInput
from ai_tools_jira.search import JiraSearchInput
from ai_tools_jira.tools import (
    tool_add_jira_comment,
    tool_create_jira_ticket,
    tool_download_jira_attachment,
    tool_get_jira_fields,
    tool_get_jira_issue,
    tool_get_jira_pull_requests,
    tool_get_jira_transitions,
    tool_search_jira,
    tool_transition_jira_issue,
    tool_update_jira_ticket,
)
from ai_tools_jira.transitions import GetJiraTransitionsInput, TransitionJiraIssueInput
from ai_tools_jira.update_ticket import UpdateJiraTicketInput


def test_tool_exports() -> None:
    """Test that tools from tools.py are properly exported.

    Requirements:
    - Tools should be importable from the main package
    - Tools should have correct names
    - Tools should have correct schemas
    - Tools should use the from_func pattern
    """
    # Test tool_get_jira_issue
    assert tool_get_jira_issue is not None
    assert tool_get_jira_issue.name == "get_jira_issue"
    assert tool_get_jira_issue.args_schema == JiraIssueInput
    assert tool_get_jira_issue.func is not None

    # Test tool_download_jira_attachment
    assert tool_download_jira_attachment is not None
    assert tool_download_jira_attachment.name == "download_jira_attachment"
    assert tool_download_jira_attachment.args_schema == JiraAttachmentDownloadInput
    assert tool_download_jira_attachment.func is not None

    # Test tool_search_jira
    assert tool_search_jira is not None
    assert tool_search_jira.name == "search_jira"
    assert tool_search_jira.args_schema == JiraSearchInput
    assert tool_search_jira.func is not None

    # Test tool_get_jira_pull_requests
    assert tool_get_jira_pull_requests is not None
    assert tool_get_jira_pull_requests.name == "get_jira_pull_requests"
    assert tool_get_jira_pull_requests.args_schema == JiraPullRequestsInput
    assert tool_get_jira_pull_requests.func is not None

    # Test tool_create_jira_ticket
    assert tool_create_jira_ticket is not None
    assert tool_create_jira_ticket.name == "create_jira_ticket"
    assert tool_create_jira_ticket.args_schema == CreateJiraTicketInput
    assert tool_create_jira_ticket.func is not None

    # Test tool_update_jira_ticket
    assert tool_update_jira_ticket is not None
    assert tool_update_jira_ticket.name == "update_jira_ticket"
    assert tool_update_jira_ticket.args_schema == UpdateJiraTicketInput
    assert tool_update_jira_ticket.func is not None

    # Test tool_add_jira_comment
    assert tool_add_jira_comment is not None
    assert tool_add_jira_comment.name == "add_jira_comment"
    assert tool_add_jira_comment.args_schema == AddJiraCommentInput
    assert tool_add_jira_comment.func is not None

    # Test tool_get_jira_fields
    assert tool_get_jira_fields is not None
    assert tool_get_jira_fields.name == "get_jira_fields"
    assert tool_get_jira_fields.args_schema == GetJiraFieldsInput
    assert tool_get_jira_fields.func is not None

    # Test tool_get_jira_transitions
    assert tool_get_jira_transitions is not None
    assert tool_get_jira_transitions.name == "get_jira_transitions"
    assert tool_get_jira_transitions.args_schema == GetJiraTransitionsInput
    assert tool_get_jira_transitions.func is not None

    # Test tool_transition_jira_issue
    assert tool_transition_jira_issue is not None
    assert tool_transition_jira_issue.name == "transition_jira_issue"
    assert tool_transition_jira_issue.args_schema == TransitionJiraIssueInput
    assert tool_transition_jira_issue.func is not None
