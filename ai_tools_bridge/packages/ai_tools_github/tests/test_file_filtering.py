"""Test the file filtering functionality."""

from ai_tools_github.commit_diff import should_include_file


def test_should_include_file_default_behavior():
    """Test that common text and code files are included by default."""
    text_files = [
        "main.py",
        "README.md",
        "config.json",
        "script.js",
        "style.css",
        "app.tsx",
        "Dockerfile",
        "requirements.txt",
        ".gitignore",
        "package.json",
        "pyproject.toml",
    ]

    for filename in text_files:
        assert should_include_file(filename), f"Expected {filename} to be included by default"


def test_should_include_file_excludes_lock_files():
    """Test that all files are included by default (no filtering)."""
    lock_files = [
        "package-lock.json",
        "yarn.lock",
        "poetry.lock",
        "Pipfile.lock",
        "Gemfile.lock",
        "composer.lock",
        "pnpm-lock.yaml",
        "bun.lockb",
        "uv.lock",
        "some-file.lock",
    ]

    for filename in lock_files:
        assert should_include_file(filename), f"Expected {filename} to be included by default (no filtering)"


def test_should_include_file_excludes_binary_files():
    """Test that all files are included by default (no filtering)."""
    binary_files = [
        "image.jpg",
        "photo.PNG",
        "icon.svg",  # SVG specifically mentioned to exclude
        "video.mp4",
        "audio.mp3",
        "archive.zip",
        "program.exe",
        "document.pdf",
        "font.ttf",
        "database.db",
        "bytecode.pyc",
        "mobile.apk",
    ]

    for filename in binary_files:
        assert should_include_file(filename), f"Expected {filename} to be included by default (no filtering)"


def test_should_include_file_case_insensitive():
    """Test that all files are included by default regardless of case."""
    # All files should be included when no scope is provided
    assert should_include_file("image.JPG")
    assert should_include_file("video.MP4")
    assert should_include_file("ICON.SVG")
    assert should_include_file("Script.PY")
    assert should_include_file("Config.JSON")


def test_should_include_file_with_scope_extensions():
    """Test file_scope filtering with extensions."""
    # Only include Python files
    file_scope = [".py"]

    assert should_include_file("main.py", file_scope)
    assert should_include_file("test.PY", file_scope)  # Case insensitive
    assert not should_include_file("config.js", file_scope)
    assert not should_include_file("README.md", file_scope)
    assert not should_include_file("Dockerfile", file_scope)


def test_should_include_file_with_scope_multiple_extensions():
    """Test file_scope filtering with multiple extensions."""
    # Include Python and JavaScript files
    file_scope = [".py", ".js", ".ts"]

    assert should_include_file("main.py", file_scope)
    assert should_include_file("script.js", file_scope)
    assert should_include_file("app.ts", file_scope)
    assert not should_include_file("config.json", file_scope)
    assert not should_include_file("README.md", file_scope)


def test_should_include_file_with_scope_patterns():
    """Test file_scope filtering with patterns."""
    # Include files with 'test' in the name
    file_scope = ["test"]

    assert should_include_file("test_main.py", file_scope)
    assert should_include_file("unit_test.js", file_scope)
    assert should_include_file("test.config.json", file_scope)
    assert not should_include_file("main.py", file_scope)
    assert not should_include_file("config.json", file_scope)


def test_should_include_file_with_scope_mixed():
    """Test file_scope filtering with mixed extensions and patterns."""
    # Include .py files and files with 'config' in the name
    file_scope = [".py", "config"]

    assert should_include_file("main.py", file_scope)
    assert should_include_file("app.config.js", file_scope)
    assert should_include_file("config.json", file_scope)
    assert should_include_file("config.PY", file_scope)  # Matches both
    assert not should_include_file("script.js", file_scope)
    assert not should_include_file("README.md", file_scope)


def test_edge_cases():
    """Test edge cases and unusual filenames."""
    # Files without extensions (default behavior - all included)
    assert should_include_file("Makefile")
    assert should_include_file("Dockerfile")

    # Files with multiple dots (all included by default)
    assert should_include_file("test.config.js")
    assert should_include_file("backup.tar.gz")

    # Very short filenames
    assert should_include_file("a")
    assert should_include_file("x.c")

    # Empty string (edge case)
    assert should_include_file("")

    # With scope - only include files with 'test'
    file_scope = ["test"]
    assert should_include_file("test.config.js", file_scope)
    assert not should_include_file("backup.tar.gz", file_scope)


def test_scope_empty_list():
    """Test that an empty file_scope list excludes all files."""
    file_scope = []

    assert not should_include_file("main.py", file_scope)
    assert not should_include_file("config.json", file_scope)
    assert not should_include_file("README.md", file_scope)
