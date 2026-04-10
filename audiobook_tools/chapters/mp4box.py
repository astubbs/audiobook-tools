"""Generate MP4Box chapter files from CUE sheets."""

import re
from pathlib import Path

from audiobook_tools.utils.time import cue_time_to_ms, ms_to_timestamp


def generate_mp4box_chapters(
    cue_file: Path,
    output_path: Path,
) -> int:
    """Generate an MP4Box chapter file from a CUE sheet.

    Args:
        cue_file: Path to the (combined) CUE file.
        output_path: Where to write the chapters file.

    Returns:
        Number of chapters written.
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

    if not chapters:
        return 0

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        for start_ms, title in chapters:
            f.write(f"{ms_to_timestamp(start_ms)} {title}\n")

    return len(chapters)
