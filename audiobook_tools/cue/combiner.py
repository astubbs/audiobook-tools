"""Combine multiple CUE sheets into a single unified CUE file.

Adjusts track numbers and timestamps so they are cumulative across
all CDs, producing a CUE sheet that matches a merged audio file.
"""

import re
from pathlib import Path

from audiobook_tools.audio.probe import get_duration_seconds
from audiobook_tools.cue.parser import CueSheet, find_cue_files, parse_cue_file
from audiobook_tools.utils.time import cue_time_to_seconds, seconds_to_cue_time


def calculate_cumulative_duration(cue_sheets: list[CueSheet], index: int) -> float:
    """Calculate the start time for a given CD by summing durations of previous CDs.

    Args:
        cue_sheets: Parsed CUE sheets in CD order.
        index: Index of the current CD (0-based).

    Returns:
        Start time in seconds for the current CD.
    """
    if index == 0:
        return 0.0

    total = 0.0
    for i in range(index):
        sheet = cue_sheets[i]
        if sheet.audio_filename is None:
            raise ValueError(f"No FILE directive found in {sheet.file_path}")
        audio_path = sheet.file_path.parent / sheet.audio_filename
        total += get_duration_seconds(audio_path)

    return total


def combine_cue_sheets(
    base_dir: Path,
    output_path: Path,
) -> None:
    """Find, parse, and combine all CUE sheets under base_dir.

    Args:
        base_dir: Directory containing CD subdirectories with CUE files.
        output_path: Where to write the combined CUE file.
    """
    cue_files = find_cue_files(base_dir)
    if not cue_files:
        print("No .cue files found. Combined file not created.")
        return

    cue_sheets = [parse_cue_file(f) for f in cue_files]
    lines: list[str] = []
    track_number = 1

    for i, sheet in enumerate(cue_sheets):
        print(f"=== Processing: {sheet.file_path} ===")
        cumulative = calculate_cumulative_duration(cue_sheets, i)

        if sheet.audio_filename:
            file_line = f'FILE "{sheet.audio_filename}" WAVE'
            lines.append(file_line)
            print(f"Added FILE: {file_line}")

        for track in sheet.tracks:
            lines.append(f"  TRACK {track_number:02d} AUDIO")
            print(f"Added TRACK {track_number}")
            track_number += 1

            if track.title and not re.match(r"^CD\s*\d+$", track.title):
                lines.append(f'    TITLE "{track.title}"')
                print(f"Added TITLE: {track.title}")

            if track.performer:
                lines.append(f'    PERFORMER "{track.performer}"')

            if track.index_time:
                original_seconds = cue_time_to_seconds(track.index_time)
                adjusted_seconds = cumulative + original_seconds
                adjusted_time = seconds_to_cue_time(adjusted_seconds)
                lines.append(f"    INDEX 01 {adjusted_time}")
                print(f"Added INDEX 01: {track.index_time} -> {adjusted_time}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Combined .cue file created: {output_path}")
