from ai_tools_base import RiskLevel, ToolDescription

from .batch_analysis import BatchPullRequestAnalysisInput, batch_analyze_pull_request
from .branch import CreateBranchInput, create_branch
from .buildsets import FetchZuulBuildsetsInput, get_zuul_buildsets_for_pr
from .code_search import CodeSearchInput, search_code
from .commit_diff import CommitDiffInput, get_commit_diff
from .commit_on_branch import (
    CreateCommitOnBranchInput,
    FileAdditionInput,
    FileDeletionInput,
    create_commit_on_branch,
)
from .create_pull_request import (
    CreatePullRequestInput,
    create_pull_request,
)
from .diff import PullRequestDiffInput, get_pull_request_diff
from .file_content import FileContentInput, get_file_content
from .issue_time_line import IssueTimeLineInput, get_issue_time_line
from .issues import CreateIssueInput, create_issue
from .issues_board import (
    FilteredProjectBoardIssuesInput,
    IssueFilters,
    ProjectFieldsInput,
    get_issues_from_project_board,
    get_project_fields,
)
from .open_issues import (
    IssueData,
    ProjectBoardIssuesInput,
    ProjectBoardIssuesOutput,
    get_open_project_board_issues,
)
from .pull_request_actions import (
    AddCommentToPullRequestInput,
    AddLabelToPullRequestInput,
    CreateReactionToPullRequestCommentInput,
    RemoveLabelFromPullRequestInput,
    add_comment_to_pull_request,
    add_label_to_pull_request,
    create_reaction_to_pull_request_comment,
    remove_label_from_pull_request,
)
from .pull_request_state import PullRequestStatusInput, get_pull_request_state
from .pull_requests import (
    AddToPullRequestDescriptionInput,
    PullRequest,
    PullRequestInput,
    SearchPullRequestsInput,
    UpdatePullRequestDescriptionInput,
    get_pull_request,
    get_pull_request_structured,
    inject_to_pull_request_description,
    search_pull_requests,
    update_pull_request_description,
)
from .pull_requests_between_commits import (
    PullRequestsBetweenCommitsInput,
    get_pull_requests_between_commits,
)
from .repo_folder_files_path import RepoFolderFilesPathInput, get_repo_folder_files_path
from .repo_history import RepoHistoryInput, get_repo_history
from .repo_stats import RepoStatsInput, get_repo_stats
from .repo_tree import RepoTreeInput, get_repo_tree

tool_get_pull_request_diff = ToolDescription.from_func(
    func=get_pull_request_diff, args_schema=PullRequestDiffInput, risk_level=RiskLevel.LOW
)
tool_get_commit_diff = ToolDescription.from_func(
    func=get_commit_diff, args_schema=CommitDiffInput, risk_level=RiskLevel.LOW
)
tool_batch_analyze_pull_request = ToolDescription.from_func(
    func=batch_analyze_pull_request, args_schema=BatchPullRequestAnalysisInput, risk_level=RiskLevel.LOW
)
tool_get_pull_requests_between_commits = ToolDescription.from_func(
    func=get_pull_requests_between_commits, args_schema=PullRequestsBetweenCommitsInput, risk_level=RiskLevel.LOW
)
tool_get_pull_request = ToolDescription.from_func(
    func=get_pull_request, args_schema=PullRequestInput, risk_level=RiskLevel.LOW
)
tool_search_pull_requests = ToolDescription.from_func(
    func=search_pull_requests, args_schema=SearchPullRequestsInput, risk_level=RiskLevel.LOW
)

tool_get_issue_time_line = ToolDescription.from_func(
    func=get_issue_time_line, args_schema=IssueTimeLineInput, risk_level=RiskLevel.LOW
)
tool_get_issues_from_project_board = ToolDescription.from_func(
    func=get_issues_from_project_board, args_schema=FilteredProjectBoardIssuesInput, risk_level=RiskLevel.LOW
)
tool_get_project_fields = ToolDescription.from_func(
    func=get_project_fields, args_schema=ProjectFieldsInput, risk_level=RiskLevel.LOW
)
tool_get_repo_history = ToolDescription.from_func(
    func=get_repo_history, args_schema=RepoHistoryInput, risk_level=RiskLevel.LOW
)
tool_get_repo_stats = ToolDescription.from_func(
    func=get_repo_stats, args_schema=RepoStatsInput, risk_level=RiskLevel.LOW
)
tool_get_repo_tree = ToolDescription.from_func(func=get_repo_tree, args_schema=RepoTreeInput, risk_level=RiskLevel.LOW)
tool_get_file_content = ToolDescription.from_func(
    func=get_file_content, args_schema=FileContentInput, risk_level=RiskLevel.LOW
)

tool_get_zuul_buildsets_for_pr = ToolDescription.from_func(
    func=get_zuul_buildsets_for_pr, args_schema=FetchZuulBuildsetsInput, risk_level=RiskLevel.LOW
)
tool_get_pull_request_structured = ToolDescription.from_func(
    func=get_pull_request_structured, args_schema=PullRequestInput, risk_level=RiskLevel.LOW
)

tool_update_pull_request_description = ToolDescription.from_func(
    func=update_pull_request_description, args_schema=UpdatePullRequestDescriptionInput, risk_level=RiskLevel.HIGH
)

tool_inject_to_pull_request_description = ToolDescription.from_func(
    func=inject_to_pull_request_description, args_schema=AddToPullRequestDescriptionInput, risk_level=RiskLevel.HIGH
)

tool_add_comment_to_pull_request = ToolDescription.from_func(
    func=add_comment_to_pull_request, args_schema=AddCommentToPullRequestInput, risk_level=RiskLevel.MEDIUM
)
tool_add_label_to_pull_request = ToolDescription.from_func(
    func=add_label_to_pull_request, args_schema=AddLabelToPullRequestInput, risk_level=RiskLevel.MEDIUM
)
tool_remove_label_from_pull_request = ToolDescription.from_func(
    func=remove_label_from_pull_request, args_schema=RemoveLabelFromPullRequestInput, risk_level=RiskLevel.MEDIUM
)

tool_create_reaction_to_pull_request_comment = ToolDescription.from_func(
    func=create_reaction_to_pull_request_comment,
    args_schema=CreateReactionToPullRequestCommentInput,
    risk_level=RiskLevel.MEDIUM,
)

tool_get_pull_request_state = ToolDescription.from_func(
    func=get_pull_request_state, args_schema=PullRequestStatusInput, risk_level=RiskLevel.LOW
)

tool_get_repo_folder_files_path = ToolDescription.from_func(
    func=get_repo_folder_files_path, args_schema=RepoFolderFilesPathInput, risk_level=RiskLevel.LOW
)
tool_create_branch = ToolDescription.from_func(
    func=create_branch, args_schema=CreateBranchInput, risk_level=RiskLevel.HIGH
)
tool_create_commit_on_branch = ToolDescription.from_func(
    func=create_commit_on_branch, args_schema=CreateCommitOnBranchInput, risk_level=RiskLevel.HIGH
)
tool_create_pull_request = ToolDescription.from_func(
    func=create_pull_request, args_schema=CreatePullRequestInput, risk_level=RiskLevel.HIGH
)
tool_create_issue = ToolDescription.from_func(
    func=create_issue, args_schema=CreateIssueInput, risk_level=RiskLevel.HIGH
)
tool_search_code = ToolDescription.from_func(func=search_code, args_schema=CodeSearchInput, risk_level=RiskLevel.LOW)

__all__ = [
    "tool_get_pull_request_diff",
    "tool_get_commit_diff",
    "tool_batch_analyze_pull_request",
    "tool_get_pull_requests_between_commits",
    "tool_get_pull_request",
    "tool_search_pull_requests",
    "tool_get_issue_time_line",
    "tool_get_issues_from_project_board",
    "tool_get_project_fields",
    "tool_get_repo_history",
    "tool_get_repo_stats",
    "tool_get_repo_tree",
    "tool_get_file_content",
    "tool_get_zuul_buildsets_for_pr",
    "tool_get_pull_request_structured",
    "tool_update_pull_request_description",
    "tool_inject_to_pull_request_description",
    "tool_add_comment_to_pull_request",
    "tool_add_label_to_pull_request",
    "tool_remove_label_from_pull_request",
    "tool_create_reaction_to_pull_request_comment",
    "tool_get_pull_request_state",
    "tool_get_repo_folder_files_path",
    "tool_create_branch",
    "tool_create_commit_on_branch",
    "tool_create_pull_request",
    "tool_create_issue",
    "tool_search_code",
    "PullRequest",
    "FileAdditionInput",
    "FileDeletionInput",
    "IssueFilters",
    # Backwards compatibility exports from open_issues
    "IssueData",
    "ProjectBoardIssuesInput",
    "ProjectBoardIssuesOutput",
    "get_open_project_board_issues",
]
