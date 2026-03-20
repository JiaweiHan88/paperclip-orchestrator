"""Convert between markdown and JIRA wiki markup formats.

This module provides functionality to convert markdown-formatted text into JIRA's
wiki markup format and vice versa, ensuring proper display in both environments.
"""

import re


def jira_to_markdown(text: str) -> str:
    """Convert JIRA wiki markup to markdown format.

    Converts common JIRA wiki markup syntax to markdown:
    - Headers: h1. Title -> # Title, h2. Title -> ## Title, etc. (h1-h6)
    - Bold: *text* -> **text**
    - Italic: _text_ -> *text*
    - Numbered lists: # item -> 1. item
    - Bullet lists: * item -> - item
    - Code blocks: {code}code{code} -> ```code```
    - Inline code: {{code}} -> `code`

    Args:
        text: JIRA wiki markup formatted text to convert.

    Returns:
        Markdown formatted text.

    Examples:
        >>> jira_to_markdown("h2. Header\\n* Bullet")
        '## Header\\n- Bullet'
        >>> jira_to_markdown("This is *bold* text")
        'This is **bold** text'
    """
    if not text:
        return text

    lines = text.split("\n")
    converted_lines: list[str] = []

    in_code_block = False

    for line in lines:
        # Handle JIRA code blocks: {code} ... {code}
        if line.strip() == "{code}":
            if not in_code_block:
                in_code_block = True
                converted_lines.append("```")
                continue
            else:
                # End of code block
                in_code_block = False
                converted_lines.append("```")
                continue

        # If we're inside a code block, don't process the line
        if in_code_block:
            converted_lines.append(line)
            continue

        # Convert headers: h1. Title -> # Title, etc.
        header_match = re.match(r"^h([1-6])\.\s+(.+)$", line)
        if header_match:
            level = int(header_match.group(1))
            content = header_match.group(2)
            line = "#" * level + " " + content
        else:
            # Convert bullet lists: * item or ** item (nested) -> - item or  - item
            # JIRA uses multiple asterisks for nesting
            bullet_match = re.match(r"^(\*+)\s+(.+)$", line)
            if bullet_match:
                asterisks = bullet_match.group(1)
                content = bullet_match.group(2)
                indent_level = len(asterisks) - 1
                indent = "  " * indent_level
                line = f"{indent}- {content}"
            else:
                # Convert numbered lists: # item or ## item (nested) -> 1. item
                numbered_match = re.match(r"^(#+)\s+(.+)$", line)
                if numbered_match:
                    hashes = numbered_match.group(1)
                    content = numbered_match.group(2)
                    indent_level = len(hashes) - 1
                    indent = "  " * indent_level
                    line = f"{indent}1. {content}"

        # Convert inline code: {{code}} -> `code`
        line = re.sub(r"\{\{(.+?)\}\}", r"`\1`", line)

        # Convert bold: *text* -> **text**
        # Need to be careful not to match bullet points or italic underscores
        # Use a function replacement to avoid conflicts with italic conversion
        def bold_replacer(match: re.Match[str]) -> str:
            return f"**{match.group(1)}**"

        line = re.sub(r"(?<!\*)\*([^*\n]+?)\*(?!\*)", bold_replacer, line)

        # Convert italic: _text_ -> *text*
        line = re.sub(r"(?<!_)_([^_\n]+?)_(?!_)", r"*\1*", line)

        converted_lines.append(line)

    # If we ended while still in a code block, close it
    if in_code_block:
        converted_lines.append("```")

    return "\n".join(converted_lines)


def markdown_to_jira(text: str) -> str:
    """Convert markdown text to JIRA wiki markup format.

    Converts common markdown syntax to JIRA wiki markup:
    - Headers: # Title -> h1. Title, ## Title -> h2. Title, etc. (h1-h6)
    - Bold: **text** or __text__ -> *text*
    - Italic: *text* or _text_ -> _text_
    - Numbered lists: 1. item -> # item
    - Bullet lists: - item or * item -> * item
    - Code blocks: ```code``` -> {code}code{code}
    - Inline code: `code` -> {{code}}

    Args:
        text: Markdown formatted text to convert.

    Returns:
        JIRA wiki markup formatted text.

    Examples:
        >>> markdown_to_jira("## Header\\n- Bullet")
        'h2. Header\\n* Bullet'
        >>> markdown_to_jira("This is **bold** text")
        'This is *bold* text'
    """
    if not text:
        return text

    lines = text.split("\n")
    converted_lines: list[str] = []

    in_code_block = False
    code_block_lines: list[str] = []

    for line in lines:
        # Handle code blocks (```)
        if line.strip().startswith("```"):
            if not in_code_block:
                in_code_block = True
                code_block_lines = []
                # Check if language is specified after ```
                continue
            else:
                # End of code block
                in_code_block = False
                if code_block_lines:
                    converted_lines.append("{code}")
                    converted_lines.extend(code_block_lines)
                    converted_lines.append("{code}")
                code_block_lines = []
                continue

        # If we're inside a code block, don't process the line
        if in_code_block:
            code_block_lines.append(line)
            continue

        # Convert headers (must be done before other conversions)
        # Check from longest to shortest to avoid partial matches
        # ###### Header -> h6. Header
        if re.match(r"^######\s+(.+)$", line):
            line = re.sub(r"^######\s+(.+)$", r"h6. \1", line)
        # ##### Header -> h5. Header
        elif re.match(r"^#####\s+(.+)$", line):
            line = re.sub(r"^#####\s+(.+)$", r"h5. \1", line)
        # #### Header -> h4. Header
        elif re.match(r"^####\s+(.+)$", line):
            line = re.sub(r"^####\s+(.+)$", r"h4. \1", line)
        # ### Header -> h3. Header
        elif re.match(r"^###\s+(.+)$", line):
            line = re.sub(r"^###\s+(.+)$", r"h3. \1", line)
        # ## Header -> h2. Header
        elif re.match(r"^##\s+(.+)$", line):
            line = re.sub(r"^##\s+(.+)$", r"h2. \1", line)
        # # Header -> h1. Header
        elif re.match(r"^#\s+(.+)$", line):
            line = re.sub(r"^#\s+(.+)$", r"h1. \1", line)

        # Convert bullet lists: - item or * item at start of line
        # Need to handle indentation for nested lists
        bullet_match = re.match(r"^(\s*)[-*]\s+(.+)$", line)
        if bullet_match:
            indent = bullet_match.group(1)
            content = bullet_match.group(2)
            # Count indentation level (2 spaces = 1 level, 4 spaces = 2 levels, etc.)
            indent_level = len(indent) // 2
            asterisks = "*" * (indent_level + 1)
            line = f"{asterisks} {content}"

        # Convert numbered lists: 1. item -> # item
        # Also handle indented numbered lists
        numbered_match = re.match(r"^(\s*)\d+\.\s+(.+)$", line)
        if numbered_match:
            indent = numbered_match.group(1)
            content = numbered_match.group(2)
            indent_level = len(indent) // 2
            hashes = "#" * (indent_level + 1)
            line = f"{hashes} {content}"

        # Convert inline code: `code` -> {{code}}
        # Use negative lookbehind and lookahead to avoid matching code blocks
        line = re.sub(r"(?<!`)`([^`]+)`(?!`)", r"{{\1}}", line)

        # Convert bold BEFORE italic to avoid conflicts
        # **text** or __text__ -> PLACEHOLDER_BOLD_START text PLACEHOLDER_BOLD_END
        # We'll use a placeholder to protect it from italic conversion
        line = re.sub(r"\*\*(.+?)\*\*", r"JIRA_BOLD_START\1JIRA_BOLD_END", line)
        line = re.sub(r"__(.+?)__", r"JIRA_BOLD_START\1JIRA_BOLD_END", line)

        # Now convert italic: *text* -> _text_
        # Single asterisks that are not at the start of line (bullet points)
        # We need to match * that has a word character or space after it (not newline)
        # and not part of our JIRA_BOLD markers
        # Pattern: not at start of line, followed by non-asterisk content, followed by *
        line = re.sub(r"(?<=\s)\*([^*\n]+?)\*(?=\s|$|[.,!?])", r"_\1_", line)

        # Convert single underscore italic (already in correct format for JIRA, but ensure consistency)
        # line = re.sub(r"(?<!_)_(?!_)([^_]+?)_(?!_)", r"_\1_", line)  # No change needed

        # Now replace the placeholders with JIRA bold format
        line = line.replace("JIRA_BOLD_START", "*")
        line = line.replace("JIRA_BOLD_END", "*")

        converted_lines.append(line)

    # If we ended while still in a code block, close it
    if in_code_block and code_block_lines:
        converted_lines.append("{code}")
        converted_lines.extend(code_block_lines)
        converted_lines.append("{code}")

    return "\n".join(converted_lines)
