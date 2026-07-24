"""Shared chapter model, CUE parsing, and format writers.

A chapter is a ``(start_ms, end_ms, title)`` tuple. Two output formats are supported:

- **FFmpeg metadata** (``;FFMETADATA1``, millisecond timebase) - used by the ffmpeg
  M4B method; needs start and end times.
- **MP4Box** (``HH:MM:SS.mmm Title`` lines) - used by the mp4box method; uses start
  times only.

Keeping the writers here means every chapter source (CUE sheets, MP3 filenames) shares
one implementation per format, and picking the format is decoupled from producing the
chapter data.
"""

from pathlib import Path

from audiobook_tools.cue.parser import parse_cue_file
from audiobook_tools.utils.time import cue_time_to_ms, ms_to_timestamp

Chapter = tuple[int, int, str]  # (start_ms, end_ms, title)


def cue_chapter_starts(cue_file: Path) -> list[tuple[int, str]]:
    """Return (start_ms, title) for each CUE track with a start time and title.

    Uses the structured parser so only track-level titles are used (an album-level
    TITLE directive is ignored).
    """
    sheet = parse_cue_file(cue_file)
    return [
        (cue_time_to_ms(track.index_time), track.title)
        for track in sheet.tracks
        if track.index_time and track.title
    ]


def with_end_times(starts: list[tuple[int, str]], final_end_ms: int) -> list[Chapter]:
    """Turn (start_ms, title) pairs into (start_ms, end_ms, title) chapters.

    Each chapter ends where the next begins; the last ends at ``final_end_ms``.
    """
    chapters: list[Chapter] = []
    for i, (start_ms, title) in enumerate(starts):
        end_ms = starts[i + 1][0] if i < len(starts) - 1 else final_end_ms
        chapters.append((start_ms, end_ms, title))
    return chapters


def write_ffmetadata(chapters: list[Chapter], output_path: Path) -> None:
    """Write chapters as an FFmpeg metadata file (millisecond timebase)."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(";FFMETADATA1\n\n")
        for start_ms, end_ms, title in chapters:
            f.write("[CHAPTER]\n")
            f.write("TIMEBASE=1/1000\n")
            f.write(f"START={start_ms}\n")
            f.write(f"END={end_ms}\n")
            f.write(f"title={title}\n\n")


def write_mp4box(chapters: list[Chapter], output_path: Path) -> None:
    """Write chapters as an MP4Box chapter file (uses start times only)."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        for start_ms, _end_ms, title in chapters:
            f.write(f"{ms_to_timestamp(start_ms)} {title}\n")
