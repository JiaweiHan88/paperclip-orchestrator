"""Tool descriptions for ai_tools_jira package."""

from ai_tools_base import RiskLevel, ToolDescription

from .add_comment import AddJiraCommentInput, add_jira_comment
from .attachment import JiraAttachmentDownloadInput, download_jira_attachment
from .create_ticket import CreateJiraTicketInput, create_jira_ticket
from .fields import GetJiraFieldsInput, get_jira_fields
from .issue import JiraIssueInput, get_jira_issue
from .link_issues import LinkJiraIssuesInput, link_jira_issues
from .pull_requests import JiraPullRequestsInput, get_jira_pull_requests
from .search import JiraSearchInput, search_jira
from .transitions import GetJiraTransitionsInput, TransitionJiraIssueInput, get_jira_transitions, transition_jira_issue
from .update_ticket import UpdateJiraTicketInput, update_jira_ticket

tool_get_jira_issue = ToolDescription.from_func(
    func=get_jira_issue, args_schema=JiraIssueInput, risk_level=RiskLevel.LOW
)
tool_download_jira_attachment = ToolDescription.from_func(
    func=download_jira_attachment, args_schema=JiraAttachmentDownloadInput, risk_level=RiskLevel.LOW
)
tool_search_jira = ToolDescription.from_func(func=search_jira, args_schema=JiraSearchInput, risk_level=RiskLevel.LOW)
tool_get_jira_pull_requests = ToolDescription.from_func(
    func=get_jira_pull_requests, args_schema=JiraPullRequestsInput, risk_level=RiskLevel.LOW
)
tool_create_jira_ticket = ToolDescription.from_func(
    func=create_jira_ticket, args_schema=CreateJiraTicketInput, risk_level=RiskLevel.MEDIUM
)
tool_update_jira_ticket = ToolDescription.from_func(
    func=update_jira_ticket, args_schema=UpdateJiraTicketInput, risk_level=RiskLevel.HIGH
)
tool_add_jira_comment = ToolDescription.from_func(
    func=add_jira_comment, args_schema=AddJiraCommentInput, risk_level=RiskLevel.MEDIUM
)
tool_get_jira_fields = ToolDescription.from_func(
    func=get_jira_fields, args_schema=GetJiraFieldsInput, risk_level=RiskLevel.LOW
)
tool_get_jira_transitions = ToolDescription.from_func(
    func=get_jira_transitions, args_schema=GetJiraTransitionsInput, risk_level=RiskLevel.LOW
)
tool_transition_jira_issue = ToolDescription.from_func(
    func=transition_jira_issue, args_schema=TransitionJiraIssueInput, risk_level=RiskLevel.MEDIUM
)
tool_link_jira_issues = ToolDescription.from_func(
    func=link_jira_issues, args_schema=LinkJiraIssuesInput, risk_level=RiskLevel.MEDIUM
)
