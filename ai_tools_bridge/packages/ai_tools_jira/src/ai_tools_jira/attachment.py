from pathlib import Path

from jira import JIRA
from pydantic import BaseModel, Field, field_validator


class JiraAttachmentDownloadInput(BaseModel):
    """Input model for downloading a Jira attachment.

    Args:
        attachment_id: The JIRA attachment ID to download.
        filename: Optional custom filename for the downloaded file. If not provided, uses the original filename.
        download_path: Optional directory path where to save the file.
            If not provided, saves to ./Jira-Attachments/<Ticket-ID>/
        ticket_id: Optional JIRA ticket ID. If not provided, will attempt to auto-detect from attachment.
    """

    attachment_id: str = Field(
        description="The JIRA attachment ID to download.",
        examples=["12345", "67890"],
    )
    download_path: str = Field(
        description="Where to save the file.",
        examples=["./downloads/file_name.jpg", "/tmp/attachments/file.txt"],
    )

    @field_validator("attachment_id")
    @classmethod
    def validate_attachment_id(cls, v: str) -> str:
        """Validate that attachment_id is not empty."""
        if not v or not v.strip():
            raise ValueError("attachment_id cannot be empty")
        return v


def download_jira_attachment(
    attachment_id: str,
    download_path: str,
    jira_instance: JIRA,
) -> str:
    """Download a JIRA attachment by ID and save it to the specified path.

    Retrieves attachment metadata and content from JIRA, then saves the file
    to the specified location. Creates parent directories if they don't exist.

    Args:
        attachment_id: The unique JIRA attachment ID to download.
        download_path: Full path where the file should be saved, including filename.
        jira_instance: Authenticated JIRA client instance.

    Returns:
        Success message containing the attachment ID, download path, file size,
        and MIME type.

    Raises:
        ValueError: If no download URL is found in the attachment metadata.
        requests.HTTPError: If the JIRA API request fails.
    """
    # Get server URL from the JIRA instance
    server_url = jira_instance._options["server"]  # pyright: ignore

    # Construct the attachment URL
    attachment_url = f"{server_url}/rest/api/2/attachment/{attachment_id}"

    # First, get attachment metadata using the JIRA session
    response = jira_instance._session.get(attachment_url)  # pyright: ignore
    response.raise_for_status()
    attachment_info = response.json()

    # Extract information from metadata
    file_size = attachment_info.get("size", 0)
    mime_type = attachment_info.get("mimeType", "application/octet-stream")
    download_url = attachment_info.get("content", "")

    if not download_url:
        raise ValueError("No download URL found in attachment metadata")

    download_dir = Path(download_path).parent

    download_dir.mkdir(parents=True, exist_ok=True)

    # Download the content using the JIRA session
    content_response = jira_instance._session.get(download_url)  # pyright: ignore
    content_response.raise_for_status()

    # Save the file
    with open(download_path, "wb") as f:
        f.write(content_response.content)

    return (
        f"Successfully downloaded attachment {attachment_id} to {download_path}. "
        f"The file has the size {file_size} and a mime type {mime_type}."
    )
