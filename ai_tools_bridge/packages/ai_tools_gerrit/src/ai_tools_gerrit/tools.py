"""ToolDescription instances for all ai_tools_gerrit tools."""

from ai_tools_base import RiskLevel, ToolDescription

from .change_actions import (
    AbandonChangeInput,
    CreateChangeInput,
    RevertChangeInput,
    RevertSubmissionInput,
    SetReadyForReviewInput,
    SetTopicInput,
    SetWorkInProgressInput,
    abandon_change,
    create_change,
    revert_change,
    revert_submission,
    set_ready_for_review,
    set_topic,
    set_work_in_progress,
)
from .change_details import (
    ChangesSubmittedTogetherInput,
    GetChangeDetailsInput,
    changes_submitted_together,
    get_change_details,
)
from .changes import (
    GetMostRecentClInput,
    QueryChangesByDateInput,
    QueryChangesInput,
    get_most_recent_cl,
    query_changes,
    query_changes_by_date,
)
from .comments import (
    ListChangeCommentsInput,
    PostReviewCommentInput,
    list_change_comments,
    post_review_comment,
)
from .commit_message import (
    GetBugsFromClInput,
    GetCommitMessageInput,
    get_bugs_from_cl,
    get_commit_message,
)
from .file_content import (
    FileContentInput,
    get_file_content,
)
from .files import (
    GetChangeDiffInput,
    GetFileDiffInput,
    ListChangeFilesInput,
    get_change_diff,
    get_file_diff,
    list_change_files,
)
from .project_branches import (
    GetProjectBranchesInput,
    get_project_branches,
)
from .reviewers import (
    AddReviewerInput,
    SuggestReviewersInput,
    add_reviewer,
    suggest_reviewers,
)
from .set_review import (
    SetReviewInput,
    set_review,
)

# ---------------------------------------------------------------------------
# Read tools (RiskLevel.LOW)
# ---------------------------------------------------------------------------

tool_query_changes = ToolDescription.from_func(
    func=query_changes, args_schema=QueryChangesInput, risk_level=RiskLevel.LOW
)

tool_query_changes_by_date = ToolDescription.from_func(
    func=query_changes_by_date, args_schema=QueryChangesByDateInput, risk_level=RiskLevel.LOW
)

tool_get_most_recent_cl = ToolDescription.from_func(
    func=get_most_recent_cl, args_schema=GetMostRecentClInput, risk_level=RiskLevel.LOW
)

tool_get_change_details = ToolDescription.from_func(
    func=get_change_details, args_schema=GetChangeDetailsInput, risk_level=RiskLevel.LOW
)

tool_changes_submitted_together = ToolDescription.from_func(
    func=changes_submitted_together,
    args_schema=ChangesSubmittedTogetherInput,
    risk_level=RiskLevel.LOW,
)

tool_get_commit_message = ToolDescription.from_func(
    func=get_commit_message, args_schema=GetCommitMessageInput, risk_level=RiskLevel.LOW
)

tool_get_bugs_from_cl = ToolDescription.from_func(
    func=get_bugs_from_cl, args_schema=GetBugsFromClInput, risk_level=RiskLevel.LOW
)

tool_list_change_files = ToolDescription.from_func(
    func=list_change_files, args_schema=ListChangeFilesInput, risk_level=RiskLevel.LOW
)

tool_get_file_diff = ToolDescription.from_func(
    func=get_file_diff, args_schema=GetFileDiffInput, risk_level=RiskLevel.LOW
)

tool_list_change_comments = ToolDescription.from_func(
    func=list_change_comments, args_schema=ListChangeCommentsInput, risk_level=RiskLevel.LOW
)

tool_suggest_reviewers = ToolDescription.from_func(
    func=suggest_reviewers, args_schema=SuggestReviewersInput, risk_level=RiskLevel.LOW
)

tool_get_file_content = ToolDescription.from_func(
    func=get_file_content, args_schema=FileContentInput, risk_level=RiskLevel.LOW
)

tool_get_project_branches = ToolDescription.from_func(
    func=get_project_branches, args_schema=GetProjectBranchesInput, risk_level=RiskLevel.LOW
)

tool_get_change_diff = ToolDescription.from_func(
    func=get_change_diff, args_schema=GetChangeDiffInput, risk_level=RiskLevel.LOW
)

# ---------------------------------------------------------------------------
# Write tools (RiskLevel.MEDIUM) — modifies review state but is reversible
# ---------------------------------------------------------------------------

tool_add_reviewer = ToolDescription.from_func(
    func=add_reviewer, args_schema=AddReviewerInput, risk_level=RiskLevel.MEDIUM
)

tool_post_review_comment = ToolDescription.from_func(
    func=post_review_comment, args_schema=PostReviewCommentInput, risk_level=RiskLevel.MEDIUM
)

tool_set_ready_for_review = ToolDescription.from_func(
    func=set_ready_for_review, args_schema=SetReadyForReviewInput, risk_level=RiskLevel.MEDIUM
)

tool_set_work_in_progress = ToolDescription.from_func(
    func=set_work_in_progress, args_schema=SetWorkInProgressInput, risk_level=RiskLevel.MEDIUM
)

tool_set_topic = ToolDescription.from_func(func=set_topic, args_schema=SetTopicInput, risk_level=RiskLevel.MEDIUM)

# ---------------------------------------------------------------------------
# Destructive / hard-to-reverse tools (RiskLevel.HIGH)
# ---------------------------------------------------------------------------

tool_create_change = ToolDescription.from_func(
    func=create_change, args_schema=CreateChangeInput, risk_level=RiskLevel.HIGH
)

tool_abandon_change = ToolDescription.from_func(
    func=abandon_change, args_schema=AbandonChangeInput, risk_level=RiskLevel.HIGH
)

tool_revert_change = ToolDescription.from_func(
    func=revert_change, args_schema=RevertChangeInput, risk_level=RiskLevel.HIGH
)

tool_revert_submission = ToolDescription.from_func(
    func=revert_submission, args_schema=RevertSubmissionInput, risk_level=RiskLevel.HIGH
)

tool_set_review = ToolDescription.from_func(func=set_review, args_schema=SetReviewInput, risk_level=RiskLevel.HIGH)

__all__ = [
    # Read
    "tool_query_changes",
    "tool_query_changes_by_date",
    "tool_get_most_recent_cl",
    "tool_get_change_details",
    "tool_changes_submitted_together",
    "tool_get_commit_message",
    "tool_get_bugs_from_cl",
    "tool_list_change_files",
    "tool_get_file_diff",
    "tool_list_change_comments",
    "tool_suggest_reviewers",
    "tool_get_file_content",
    "tool_get_project_branches",
    "tool_get_change_diff",
    # Write (medium)
    "tool_add_reviewer",
    "tool_post_review_comment",
    "tool_set_ready_for_review",
    "tool_set_work_in_progress",
    "tool_set_topic",
    # Destructive (high)
    "tool_create_change",
    "tool_abandon_change",
    "tool_revert_change",
    "tool_revert_submission",
    "tool_set_review",
]
