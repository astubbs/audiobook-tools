"""Generate chapter metadata from a list of MP3 files.

Chapter titles are derived from filenames; each chapter spans one MP3 file, with
cumulative start/end times computed from the files' durations. Output is an
FFmpeg metadata (``;FFMETADATA1``) file with millisecond timebase.

The caller must pass files in playback order (the same order they are concatenated
into the combined audio), so chapter timestamps align with the audio. Use
:func:`audiobook_tools.audio.merge.ordered_mp3_files` to produce that ordering.
"""

import re
from pathlib import Path

from audiobook_tools.audio.probe import get_duration_ms
from audiobook_tools.chapters._common import Chapter, write_ffmetadata, write_mp4box

# Strip a leading "CD<n>" prefix and/or a leading track number from a filename
# stem, e.g. "CD1 - 03 - The River" -> "The River", "02 - Introduction" ->
# "Introduction". Separators may be any of - _ . or spaces.
_PREFIX_RE = re.compile(r"^(?:cd\s*\d+\s*[-_.\s]+)?(?:\d+\s*[-_.\s]+)?", re.IGNORECASE)


def title_from_filename(path: Path) -> str:
    """Extract a chapter title from an MP3 filename.

    Removes a leading CD prefix and/or track number. Falls back to the full stem
    if stripping would leave the title empty.
    """
    stem = path.stem
    title = _PREFIX_RE.sub("", stem).strip()
    return title or stem


def mp3_chapter_list(mp3_files: list[Path]) -> list[Chapter]:
    """Build (start_ms, end_ms, title) chapters from MP3 files in playback order.

    Files whose duration cannot be determined (<= 0) are skipped. Duplicate chapter
    titles are disambiguated: the first occurrence is left as-is and later ones get a
    `` (2)``, `` (3)`` suffix.
    """
    chapters: list[Chapter] = []
    seen: dict[str, int] = {}
    current_ms = 0

    for mp3_file in mp3_files:
        duration_ms = get_duration_ms(mp3_file)
        if duration_ms <= 0:
            continue

        title = title_from_filename(mp3_file)
        if title in seen:
            seen[title] += 1
            title = f"{title} ({seen[title]})"
        else:
            seen[title] = 1

        chapters.append((current_ms, current_ms + duration_ms, title))
        current_ms += duration_ms

    return chapters


def generate_mp3_chapters(mp3_files: list[Path], output_path: Path, method: str = "ffmpeg") -> int:
    """Write a chapter file for ``mp3_files`` (in playback order).

    ``method`` selects the output format: ``"ffmpeg"`` writes FFMETADATA1, ``"mp4box"``
    writes an MP4Box chapter file. Returns the number of chapters written.
    """
    chapters = mp3_chapter_list(mp3_files)
    if not chapters:
        return 0

    if method == "mp4box":
        write_mp4box(chapters, output_path)
    else:
        write_ffmetadata(chapters, output_path)
    return len(chapters)
