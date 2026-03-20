from ai_tools_base import RiskLevel, ToolDescription

from .add_comment import AddConfluenceCommentInput, add_confluence_comment
from .create_page import CreateConfluencePageInput, create_confluence_page
from .page import (
    GetConfluencePageByIdHtmlInput,
    GetConfluencePageByIdInput,
    GetConfluencePageByTitleHtmlInput,
    GetConfluencePageByTitleInput,
    get_confluence_page_by_id,
    get_confluence_page_by_id_html,
    get_confluence_page_by_title,
    get_confluence_page_by_title_html,
)
from .page_relocation import (
    RelocateConfluencePageInput,
    relocate_confluence_page,
)
from .search import (
    ConfluenceCQLSearchInput,
    ConfluenceFreeTextSearchInput,
    search_confluence_pages_freetext,
    search_confluence_with_cql,
)
from .space import (
    GetConfluencePageTreeInput,
    GetConfluenceSpacesInput,
    get_confluence_page_tree,
    get_confluence_spaces,
)
from .update_page import UpdateConfluencePageInput, update_confluence_page

tool_get_confluence_page_by_id = ToolDescription.from_func(
    func=get_confluence_page_by_id,
    args_schema=GetConfluencePageByIdInput,
    risk_level=RiskLevel.LOW,
)
tool_get_confluence_page_by_title = ToolDescription.from_func(
    func=get_confluence_page_by_title,
    args_schema=GetConfluencePageByTitleInput,
    risk_level=RiskLevel.LOW,
)
tool_get_confluence_page_by_id_html = ToolDescription.from_func(
    func=get_confluence_page_by_id_html,
    args_schema=GetConfluencePageByIdHtmlInput,
    risk_level=RiskLevel.LOW,
)
tool_get_confluence_page_by_title_html = ToolDescription.from_func(
    func=get_confluence_page_by_title_html,
    args_schema=GetConfluencePageByTitleHtmlInput,
    risk_level=RiskLevel.LOW,
)
tool_search_confluence_with_cql = ToolDescription.from_func(
    func=search_confluence_with_cql,
    args_schema=ConfluenceCQLSearchInput,
    risk_level=RiskLevel.LOW,
)
tool_search_confluence_pages_freetext = ToolDescription.from_func(
    func=search_confluence_pages_freetext,
    args_schema=ConfluenceFreeTextSearchInput,
    risk_level=RiskLevel.LOW,
)
tool_get_confluence_spaces = ToolDescription.from_func(
    func=get_confluence_spaces,
    args_schema=GetConfluenceSpacesInput,
    risk_level=RiskLevel.LOW,
)
tool_get_confluence_page_tree = ToolDescription.from_func(
    func=get_confluence_page_tree,
    args_schema=GetConfluencePageTreeInput,
    risk_level=RiskLevel.LOW,
)
tool_update_confluence_page = ToolDescription.from_func(
    func=update_confluence_page,
    args_schema=UpdateConfluencePageInput,
    risk_level=RiskLevel.HIGH,
)
tool_create_confluence_page = ToolDescription.from_func(
    func=create_confluence_page,
    args_schema=CreateConfluencePageInput,
    risk_level=RiskLevel.MEDIUM,
)
tool_add_confluence_comment = ToolDescription.from_func(
    func=add_confluence_comment,
    args_schema=AddConfluenceCommentInput,
    risk_level=RiskLevel.MEDIUM,
)
tool_relocate_confluence_page = ToolDescription.from_func(
    func=relocate_confluence_page,
    args_schema=RelocateConfluencePageInput,
    risk_level=RiskLevel.HIGH,
)

__all__ = [
    # Read-only tools (RiskLevel.LOW)
    "GetConfluencePageByIdInput",
    "get_confluence_page_by_id",
    "tool_get_confluence_page_by_id",
    "GetConfluencePageByTitleInput",
    "get_confluence_page_by_title",
    "tool_get_confluence_page_by_title",
    "GetConfluencePageByIdHtmlInput",
    "get_confluence_page_by_id_html",
    "tool_get_confluence_page_by_id_html",
    "GetConfluencePageByTitleHtmlInput",
    "get_confluence_page_by_title_html",
    "tool_get_confluence_page_by_title_html",
    "ConfluenceCQLSearchInput",
    "search_confluence_with_cql",
    "tool_search_confluence_with_cql",
    "ConfluenceFreeTextSearchInput",
    "search_confluence_pages_freetext",
    "tool_search_confluence_pages_freetext",
    "GetConfluenceSpacesInput",
    "get_confluence_spaces",
    "tool_get_confluence_spaces",
    "GetConfluencePageTreeInput",
    "get_confluence_page_tree",
    "tool_get_confluence_page_tree",
    # Write/Edit tools (RiskLevel.MEDIUM/HIGH)
    "UpdateConfluencePageInput",
    "update_confluence_page",
    "tool_update_confluence_page",
    "CreateConfluencePageInput",
    "create_confluence_page",
    "tool_create_confluence_page",
    "AddConfluenceCommentInput",
    "add_confluence_comment",
    "tool_add_confluence_comment",
    "RelocateConfluencePageInput",
    "relocate_confluence_page",
    "tool_relocate_confluence_page",
]
