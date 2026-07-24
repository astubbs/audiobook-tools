"""CUE sheet parsing.

Parses CUE files into structured data, handling FILE, TRACK, TITLE,
PERFORMER, and INDEX directives.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class CueTrack:
    """A single track from a CUE sheet."""

    number: int
    title: str | None = None
    performer: str | None = None
    index_time: str | None = None  # MM:SS:FF format


@dataclass
class CueSheet:
    """Parsed contents of a CUE file."""

    file_path: Path  # path to the CUE file itself
    audio_filename: str | None = None  # the FILE directive value
    performer: str | None = None  # album-level performer
    tracks: list[CueTrack] = field(default_factory=list)


def parse_cue_file(path: Path) -> CueSheet:
    """Parse a CUE file into a CueSheet."""
    content = path.read_text(encoding="utf-8")
    lines = content.splitlines()

    sheet = CueSheet(file_path=path)
    current_track: CueTrack | None = None

    for line in lines:
        stripped = line.strip()

        if stripped.startswith("FILE"):
            match = re.search(r'FILE\s+"([^"]+)"', stripped)
            if match:
                sheet.audio_filename = match.group(1)

        elif stripped.startswith("TRACK"):
            match = re.match(r"TRACK\s+(\d+)\s+AUDIO", stripped)
            if match:
                current_track = CueTrack(number=int(match.group(1)))
                sheet.tracks.append(current_track)

        elif stripped.startswith("TITLE"):
            match = re.search(r'TITLE\s+"([^"]*)"', stripped)
            if match:
                title = match.group(1)
                if current_track is not None:
                    current_track.title = title

        elif stripped.startswith("PERFORMER"):
            match = re.search(r'PERFORMER\s+"([^"]*)"', stripped)
            if match:
                performer = match.group(1)
                if current_track is not None:
                    current_track.performer = performer
                else:
                    sheet.performer = performer

        elif stripped.startswith("INDEX"):
            match = re.search(r"INDEX\s+01\s+(\d{2}:\d{2}:\d{2})", stripped)
            if match and current_track is not None:
                current_track.index_time = match.group(1)

    return sheet


def find_cue_files(base_dir: Path) -> list[Path]:
    """Find all .cue files under base_dir, sorted by CD number."""
    cue_files = sorted(base_dir.rglob("*.cue"), key=_cd_sort_key)
    return cue_files


def _cd_sort_key(path: Path) -> int:
    """Extract CD number from a path for sorting."""
    match = re.search(r"CD(\d+)", str(path))
    return int(match.group(1)) if match else 0
