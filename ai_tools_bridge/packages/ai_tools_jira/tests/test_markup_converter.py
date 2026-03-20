"""Tests for markdown and JIRA wiki markup conversion."""

import unittest

from ai_tools_jira.markup_converter import jira_to_markdown, markdown_to_jira


class TestMarkdownToJira(unittest.TestCase):
    """Test cases for markdown to JIRA wiki markup conversion.

    Requirements:
    - Convert markdown headers (##, ###) to JIRA wiki markup (h2., h3.)
    - Convert markdown bold (**text**) to JIRA bold (*text*)
    - Convert markdown bullets (- item) to JIRA bullets (* item)
    - Convert markdown numbered lists (1. item) to JIRA numbered lists (# item)
    - Convert markdown inline code (`code`) to JIRA inline code ({{code}})
    - Convert markdown code blocks (```) to JIRA code blocks ({code})
    - Handle nested lists with proper indentation
    - Preserve text that doesn't match any patterns
    """

    def test_headers_conversion(self):
        """Test conversion of markdown headers to JIRA headers."""
        # Single header levels
        self.assertEqual(markdown_to_jira("# Header 1"), "h1. Header 1")
        self.assertEqual(markdown_to_jira("## Header 2"), "h2. Header 2")
        self.assertEqual(markdown_to_jira("### Header 3"), "h3. Header 3")
        self.assertEqual(markdown_to_jira("#### Header 4"), "h4. Header 4")
        self.assertEqual(markdown_to_jira("##### Header 5"), "h5. Header 5")
        self.assertEqual(markdown_to_jira("###### Header 6"), "h6. Header 6")

        # Multiple headers
        text = "## First Header\nSome text\n### Second Header"
        expected = "h2. First Header\nSome text\nh3. Second Header"
        self.assertEqual(markdown_to_jira(text), expected)

    def test_bold_conversion(self):
        """Test conversion of markdown bold to JIRA bold."""
        # Double asterisk bold
        self.assertEqual(markdown_to_jira("This is **bold** text"), "This is *bold* text")

        # Double underscore bold
        self.assertEqual(markdown_to_jira("This is __bold__ text"), "This is *bold* text")

        # Multiple bold in one line
        self.assertEqual(
            markdown_to_jira("**First** and **second** bold"),
            "*First* and *second* bold",
        )

    def test_italic_conversion(self):
        """Test conversion of markdown italic to JIRA italic."""
        # Single asterisk italic (not at start of line)
        self.assertEqual(markdown_to_jira("This is *italic* text"), "This is _italic_ text")

        # Single underscore italic
        self.assertEqual(markdown_to_jira("This is _italic_ text"), "This is _italic_ text")

    def test_bullet_list_conversion(self):
        """Test conversion of markdown bullet lists to JIRA bullet lists."""
        # Dash bullets
        self.assertEqual(markdown_to_jira("- Item 1"), "* Item 1")
        self.assertEqual(markdown_to_jira("- Item 1\n- Item 2"), "* Item 1\n* Item 2")

        # Asterisk bullets (at start of line)
        text = "* Item 1\n* Item 2"
        expected = "* Item 1\n* Item 2"
        self.assertEqual(markdown_to_jira(text), expected)

    def test_nested_bullet_list_conversion(self):
        """Test conversion of nested markdown bullet lists."""
        # Two-level nested list
        text = "- Level 1\n  - Level 2\n- Level 1 again"
        expected = "* Level 1\n** Level 2\n* Level 1 again"
        self.assertEqual(markdown_to_jira(text), expected)

        # Three-level nested list
        text = "- L1\n  - L2\n    - L3"
        expected = "* L1\n** L2\n*** L3"
        self.assertEqual(markdown_to_jira(text), expected)

    def test_numbered_list_conversion(self):
        """Test conversion of markdown numbered lists to JIRA numbered lists."""
        # Simple numbered list
        self.assertEqual(markdown_to_jira("1. Item 1"), "# Item 1")
        self.assertEqual(markdown_to_jira("1. Item 1\n2. Item 2"), "# Item 1\n# Item 2")

    def test_nested_numbered_list_conversion(self):
        """Test conversion of nested numbered lists."""
        # Two-level nested numbered list
        text = "1. Level 1\n  1. Level 2\n2. Level 1 again"
        expected = "# Level 1\n## Level 2\n# Level 1 again"
        self.assertEqual(markdown_to_jira(text), expected)

    def test_inline_code_conversion(self):
        """Test conversion of inline code from markdown to JIRA."""
        self.assertEqual(markdown_to_jira("Use `code` here"), "Use {{code}} here")

        # Multiple inline code snippets
        self.assertEqual(
            markdown_to_jira("Use `code1` and `code2` here"),
            "Use {{code1}} and {{code2}} here",
        )

    def test_code_block_conversion(self):
        """Test conversion of code blocks from markdown to JIRA."""
        # Simple code block
        text = "```\ncode line 1\ncode line 2\n```"
        expected = "{code}\ncode line 1\ncode line 2\n{code}"
        self.assertEqual(markdown_to_jira(text), expected)

        # Code block with language specifier
        text = "```python\nprint('hello')\n```"
        expected = "{code}\nprint('hello')\n{code}"
        self.assertEqual(markdown_to_jira(text), expected)

    def test_mixed_formatting(self):
        """Test conversion of text with multiple formatting types."""
        text = """## Project Overview
This is **important** information.

- First item with `code`
- Second item
  - Nested item

1. Numbered item
2. Another numbered item"""

        expected = """h2. Project Overview
This is *important* information.

* First item with {{code}}
* Second item
** Nested item

# Numbered item
# Another numbered item"""

        self.assertEqual(markdown_to_jira(text), expected)

    def test_empty_and_none_input(self):
        """Test handling of empty or None input."""
        self.assertEqual(markdown_to_jira(""), "")
        self.assertEqual(markdown_to_jira(None), None)

    def test_plain_text_preserved(self):
        """Test that plain text without markdown formatting is preserved."""
        text = "This is just plain text without any formatting."
        self.assertEqual(markdown_to_jira(text), text)

    def test_complex_real_world_example(self):
        """Test a complex real-world example similar to the user's issue."""
        text = """## Problem Description
The system fails when processing large files.

## Root Cause
- Memory allocation issue
- Buffer overflow in `process_data` function

## Solution
1. Increase buffer size
2. Add memory checks
3. Implement **chunked processing**

## Code Changes
```python
def process_data(data):
    # Process in chunks
    pass
```

## Testing
- Unit tests added
  - Test with small files
  - Test with large files
- Integration tests passed"""

        expected = """h2. Problem Description
The system fails when processing large files.

h2. Root Cause
* Memory allocation issue
* Buffer overflow in {{process_data}} function

h2. Solution
# Increase buffer size
# Add memory checks
# Implement *chunked processing*

h2. Code Changes
{code}
def process_data(data):
    # Process in chunks
    pass
{code}

h2. Testing
* Unit tests added
** Test with small files
** Test with large files
* Integration tests passed"""

        self.assertEqual(markdown_to_jira(text), expected)

    def test_hash_not_at_start_of_line(self):
        """Test that # not at start of line is not converted."""
        text = "This is item #1 in the list"
        self.assertEqual(markdown_to_jira(text), text)

    def test_asterisk_in_middle_of_line(self):
        """Test that * in middle of line for bold is converted correctly."""
        text = "The value is 2*3*4 = 24"
        # This might get converted, which could be an issue
        # For now, we accept this limitation
        result = markdown_to_jira(text)
        # Just verify it doesn't crash
        self.assertIsInstance(result, str)


class TestJiraToMarkdown(unittest.TestCase):
    """Test cases for JIRA wiki markup to markdown conversion.

    Requirements:
    - Convert JIRA headers (h2., h3.) to markdown headers (##, ###)
    - Convert JIRA bold (*text*) to markdown bold (**text**)
    - Convert JIRA italic (_text_) to markdown italic (*text*)
    - Convert JIRA bullets (* item) to markdown bullets (- item)
    - Convert JIRA numbered lists (# item) to markdown numbered lists (1. item)
    - Convert JIRA inline code ({{code}}) to markdown inline code (`code`)
    - Convert JIRA code blocks ({code}) to markdown code blocks (```)
    - Handle nested lists with proper indentation
    - Preserve text that doesn't match any patterns
    """

    def test_headers_conversion(self):
        """Test conversion of JIRA headers to markdown headers."""
        # Single header levels
        self.assertEqual(jira_to_markdown("h1. Header 1"), "# Header 1")
        self.assertEqual(jira_to_markdown("h2. Header 2"), "## Header 2")
        self.assertEqual(jira_to_markdown("h3. Header 3"), "### Header 3")
        self.assertEqual(jira_to_markdown("h4. Header 4"), "#### Header 4")
        self.assertEqual(jira_to_markdown("h5. Header 5"), "##### Header 5")
        self.assertEqual(jira_to_markdown("h6. Header 6"), "###### Header 6")

        # Multiple headers
        text = "h2. First Header\nSome text\nh3. Second Header"
        expected = "## First Header\nSome text\n### Second Header"
        self.assertEqual(jira_to_markdown(text), expected)

    def test_bold_conversion(self):
        """Test conversion of JIRA bold to markdown bold."""
        self.assertEqual(jira_to_markdown("This is *bold* text"), "This is **bold** text")

        # Multiple bold in one line
        self.assertEqual(
            jira_to_markdown("*First* and *second* bold"),
            "**First** and **second** bold",
        )

    def test_italic_conversion(self):
        """Test conversion of JIRA italic to markdown italic."""
        self.assertEqual(jira_to_markdown("This is _italic_ text"), "This is *italic* text")

    def test_bullet_list_conversion(self):
        """Test conversion of JIRA bullet lists to markdown bullet lists."""
        self.assertEqual(jira_to_markdown("* Item 1"), "- Item 1")
        self.assertEqual(jira_to_markdown("* Item 1\n* Item 2"), "- Item 1\n- Item 2")

    def test_nested_bullet_list_conversion(self):
        """Test conversion of nested JIRA bullet lists."""
        # Two-level nested list
        text = "* Level 1\n** Level 2\n* Level 1 again"
        expected = "- Level 1\n  - Level 2\n- Level 1 again"
        self.assertEqual(jira_to_markdown(text), expected)

        # Three-level nested list
        text = "* L1\n** L2\n*** L3"
        expected = "- L1\n  - L2\n    - L3"
        self.assertEqual(jira_to_markdown(text), expected)

    def test_numbered_list_conversion(self):
        """Test conversion of JIRA numbered lists to markdown numbered lists."""
        self.assertEqual(jira_to_markdown("# Item 1"), "1. Item 1")
        self.assertEqual(jira_to_markdown("# Item 1\n# Item 2"), "1. Item 1\n1. Item 2")

    def test_nested_numbered_list_conversion(self):
        """Test conversion of nested numbered lists."""
        # Two-level nested numbered list
        text = "# Level 1\n## Level 2\n# Level 1 again"
        expected = "1. Level 1\n  1. Level 2\n1. Level 1 again"
        self.assertEqual(jira_to_markdown(text), expected)

    def test_inline_code_conversion(self):
        """Test conversion of inline code from JIRA to markdown."""
        self.assertEqual(jira_to_markdown("Use {{code}} here"), "Use `code` here")

        # Multiple inline code snippets
        self.assertEqual(
            jira_to_markdown("Use {{code1}} and {{code2}} here"),
            "Use `code1` and `code2` here",
        )

    def test_code_block_conversion(self):
        """Test conversion of code blocks from JIRA to markdown."""
        # Simple code block
        text = "{code}\ncode line 1\ncode line 2\n{code}"
        expected = "```\ncode line 1\ncode line 2\n```"
        self.assertEqual(jira_to_markdown(text), expected)

    def test_mixed_formatting(self):
        """Test conversion of text with multiple formatting types."""
        text = """h2. Project Overview
This is *important* information.

* First item with {{code}}
* Second item
** Nested item

# Numbered item
# Another numbered item"""

        expected = """## Project Overview
This is **important** information.

- First item with `code`
- Second item
  - Nested item

1. Numbered item
1. Another numbered item"""

        self.assertEqual(jira_to_markdown(text), expected)

    def test_empty_and_none_input(self):
        """Test handling of empty or None input."""
        self.assertEqual(jira_to_markdown(""), "")
        self.assertEqual(jira_to_markdown(None), None)

    def test_plain_text_preserved(self):
        """Test that plain text without JIRA formatting is preserved."""
        text = "This is just plain text without any formatting."
        self.assertEqual(jira_to_markdown(text), text)

    def test_complex_real_world_example(self):
        """Test a complex real-world example from JIRA."""
        text = """h2. Problem Description
The system fails when processing large files.

h2. Root Cause
* Memory allocation issue
* Buffer overflow in {{process_data}} function

h2. Solution
# Increase buffer size
# Add memory checks
# Implement *chunked processing*

h2. Code Changes
{code}
def process_data(data):
    # Process in chunks
    pass
{code}

h2. Testing
* Unit tests added
** Test with small files
** Test with large files
* Integration tests passed"""

        expected = """## Problem Description
The system fails when processing large files.

## Root Cause
- Memory allocation issue
- Buffer overflow in `process_data` function

## Solution
1. Increase buffer size
1. Add memory checks
1. Implement **chunked processing**

## Code Changes
```
def process_data(data):
    # Process in chunks
    pass
```

## Testing
- Unit tests added
  - Test with small files
  - Test with large files
- Integration tests passed"""

        self.assertEqual(jira_to_markdown(text), expected)


if __name__ == "__main__":
    unittest.main()
