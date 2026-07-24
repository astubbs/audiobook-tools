"""Generate FFmpeg metadata chapter files from CUE sheets."""

from pathlib import Path

from audiobook_tools.audio.probe import get_duration_ms
from audiobook_tools.chapters._common import (
    cue_chapter_starts,
    with_end_times,
    write_ffmetadata,
)


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
    starts = cue_chapter_starts(cue_file)
    if not starts:
        return 0

    chapters = with_end_times(starts, get_duration_ms(audio_file))
    write_ffmetadata(chapters, output_path)
    return len(chapters)
