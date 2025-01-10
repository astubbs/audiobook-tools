"""Common data classes and utilities for audiobook tools."""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class AudiobookMetadata:
    """Metadata for an audiobook."""

    title: Optional[str] = None
    artist: Optional[str] = None
    cover_art: Optional[Path] = None

    def has_required_metadata(self) -> bool:
        """Check if the required metadata fields are present."""
        return bool(self.title and self.artist)
