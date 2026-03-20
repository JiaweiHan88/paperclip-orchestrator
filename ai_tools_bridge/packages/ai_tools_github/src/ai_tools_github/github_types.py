"""Local types replacing gitaudit.github.graphql_objects and gitaudit.github.instance types."""

import base64
from dataclasses import dataclass
from enum import StrEnum


@dataclass
class FileAddition:
    """A file addition for a commit."""

    path: str
    contents: str  # base64 encoded

    @classmethod
    def from_plain_text(cls, path: str, content: str) -> "FileAddition":
        """Create a FileAddition from plain text content."""
        encoded = base64.b64encode(content.encode()).decode()
        return cls(path=path, contents=encoded)


@dataclass
class FileDeletion:
    """A file deletion for a commit."""

    path: str


class CheckConclusionState(StrEnum):
    """GitHub check run conclusion states."""

    ACTION_REQUIRED = "ACTION_REQUIRED"
    CANCELLED = "CANCELLED"
    FAILURE = "FAILURE"
    NEUTRAL = "NEUTRAL"
    SKIPPED = "SKIPPED"
    STALE = "STALE"
    STARTUP_FAILURE = "STARTUP_FAILURE"
    SUCCESS = "SUCCESS"
    TIMED_OUT = "TIMED_OUT"


class CheckStatusState(StrEnum):
    """GitHub check run status states."""

    COMPLETED = "COMPLETED"
    IN_PROGRESS = "IN_PROGRESS"
    PENDING = "PENDING"
    QUEUED = "QUEUED"
    REQUESTED = "REQUESTED"
    WAITING = "WAITING"


class Reaction(StrEnum):
    """GitHub comment reaction types."""

    THUMBS_UP = "THUMBS_UP"
    THUMBS_DOWN = "THUMBS_DOWN"
    LAUGH = "LAUGH"
    HOORAY = "HOORAY"
    CONFUSED = "CONFUSED"
    HEART = "HEART"
    ROCKET = "ROCKET"
    EYES = "EYES"
