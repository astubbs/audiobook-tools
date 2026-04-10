"""Generate FFmpeg metadata chapter files from CUE sheets."""

import re
from pathlib import Path

from audiobook_tools.audio.probe import get_duration_ms
from audiobook_tools.utils.time import cue_time_to_ms


def generate_ffmetadata(
    cue_file: Path,
    audio_file: Path,
    output_path: Path,
) -> int:
    """Generate an FFmpeg metadata chapter file from a CUE sheet.

    Args:
        cue_file: Path to the (combined) CUE file.
        audio_file: Path to the audio file (for last chapter end time).
        output_path: Where to write the FFMETADATA1 file.

    Returns:
        Number of chapters written.
    """
    chapters = _parse_chapters_from_cue(cue_file)
    if not chapters:
        return 0

    duration_ms = get_duration_ms(audio_file)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(";FFMETADATA1\n\n")

        for i, (start_ms, title) in enumerate(chapters):
            end_ms = chapters[i + 1][0] if i < len(chapters) - 1 else duration_ms
            f.write("[CHAPTER]\n")
            f.write("TIMEBASE=1/1000\n")
            f.write(f"START={start_ms}\n")
            f.write(f"END={end_ms}\n")
            f.write(f"title={title}\n\n")

    return len(chapters)


def _parse_chapters_from_cue(cue_file: Path) -> list[tuple[int, str]]:
    """Parse chapter start times and titles from a CUE file.

    Returns list of (start_ms, title) tuples.
    """
    lines = cue_file.read_text(encoding="utf-8").splitlines()
    chapters: list[tuple[int, str]] = []
    current_title: str | None = None

    for line in lines:
        if "TITLE" in line:
            match = re.search(r'TITLE\s+"([^"]*)"', line)
            if match:
                current_title = match.group(1)
        elif "INDEX 01" in line and current_title:
            match = re.search(r"INDEX 01 (\d+:\d+:\d+)", line)
            if match:
                start_ms = cue_time_to_ms(match.group(1))
                chapters.append((start_ms, current_title))

    return chapters
