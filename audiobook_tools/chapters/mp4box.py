"""Generate MP4Box chapter files from CUE sheets."""

from pathlib import Path

from audiobook_tools.chapters._common import (
    cue_chapter_starts,
    with_end_times,
    write_mp4box,
)


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
    starts = cue_chapter_starts(cue_file)
    if not starts:
        return 0

    # MP4Box uses only start times; the final end time is unused, so reuse the last
    # start as a placeholder.
    chapters = with_end_times(starts, starts[-1][0])
    write_mp4box(chapters, output_path)
    return len(chapters)
