def filter_large_diff_chunks(git_diff: str, max_lines: int = 1000) -> str:
    """
    Process a git diff string to remove chunks that exceed the specified line limit.

    Args:
        git_diff: The complete git diff as a string
        max_lines: Maximum number of lines allowed in a diff chunk (default: 1000)

    Returns:
        Filtered git diff with large chunks removed
    """
    # Split the diff into individual file diffs
    file_diffs = split_diff_by_files(git_diff)

    # Process each file diff to remove large chunks
    filtered_file_diffs: list[str] = []
    for file_diff in file_diffs:
        filtered_diff = filter_chunks_in_file_diff(file_diff, max_lines)
        if filtered_diff.strip():  # Only include if there's content left
            filtered_file_diffs.append(filtered_diff)

    return "\n".join(filtered_file_diffs)


def split_diff_by_files(git_diff: str) -> list[str]:
    """
    Split a git diff string into individual file diffs.

    Args:
        git_diff: The complete git diff as a string

    Returns:
        List of individual file diff strings
    """
    # Split by lines that start with "diff --git"
    lines = git_diff.split("\n")
    file_diffs: list[str] = []
    current_diff: list[str] = []

    for line in lines:
        if line.startswith("diff --git"):
            # If we have a current diff, save it
            if current_diff:
                file_diffs.append("\n".join(current_diff))
                current_diff = []
        current_diff.append(line)

    # Don't forget the last diff
    if current_diff:
        file_diffs.append("\n".join(current_diff))

    return file_diffs


def filter_chunks_in_file_diff(file_diff: str, max_lines: int) -> str:
    """
    Filter chunks within a single file diff, removing those that exceed max_lines.

    Args:
        file_diff: A single file's diff content
        max_lines: Maximum number of lines allowed in a chunk

    Returns:
        Filtered file diff with large chunks removed
    """
    lines = file_diff.split("\n")

    # Find the header (everything before the first @@ line)
    header_lines: list[str] = []
    content_start_idx = 0

    for i, line in enumerate(lines):
        if line.startswith("@@"):
            content_start_idx = i
            break
        header_lines.append(line)

    # If no @@ found, return the original (probably not a proper diff)
    if content_start_idx == 0:
        return file_diff

    # Split the content into chunks by @@ markers
    chunks = split_diff_chunks(lines[content_start_idx:])

    # Filter chunks by size
    filtered_chunks: list[list[str]] = []
    for chunk in chunks:
        chunk_size = count_diff_lines(chunk)
        if chunk_size <= max_lines:
            filtered_chunks.append(chunk)

    # Reconstruct the diff
    if not filtered_chunks:
        # If all chunks were too large, return just the header
        return "\n".join(header_lines)

    result_lines: list[str] = header_lines + []
    for chunk in filtered_chunks:
        result_lines.extend(chunk)

    return "\n".join(result_lines)


def split_diff_chunks(content_lines: list[str]) -> list[list[str]]:
    """
    Split diff content into chunks separated by @@ markers.

    Args:
        content_lines: Lines of diff content starting from the first @@

    Returns:
        List of chunks, where each chunk is a list of lines
    """
    chunks: list[list[str]] = []
    current_chunk: list[str] = []

    for line in content_lines:
        if line.startswith("@@"):
            # If we have a current chunk, save it
            if current_chunk:
                chunks.append(current_chunk)
                current_chunk = []
        current_chunk.append(line)

    # Don't forget the last chunk
    if current_chunk:
        chunks.append(current_chunk)

    return chunks


def count_diff_lines(chunk: list[str]) -> int:
    """
    Count the number of actual diff lines (+ and - lines) in a chunk.

    Args:
        chunk: List of lines in a diff chunk

    Returns:
        Number of lines that represent actual changes
    """
    count = 0
    for line in chunk:
        # Skip the @@ header line and context lines that don't start with + or -
        if line.startswith(("+", "-")) and not line.startswith(("+++", "---")):
            count += 1
    return count
