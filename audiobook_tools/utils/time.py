"""Time conversion utilities for audiobook processing.

Handles conversions between CUE sheet time format (MM:SS:FF where FF is
CD frames at 75 fps), milliseconds, seconds, and MP4Box timestamp format.
"""


def cue_time_to_ms(cue_time: str) -> int:
    """Convert CUE time (MM:SS:FF) to milliseconds.

    In CD audio, there are exactly 75 frames per second.
    """
    minutes, seconds, frames = map(int, cue_time.split(":"))
    total_ms = (minutes * 60 + seconds) * 1000 + (frames * 1000 // 75)
    return total_ms


def cue_time_to_seconds(cue_time: str) -> float:
    """Convert CUE time (MM:SS:FF) to seconds."""
    minutes, seconds, frames = map(int, cue_time.split(":"))
    return minutes * 60 + seconds + frames / 75.0


def seconds_to_cue_time(total_seconds: float) -> str:
    """Convert seconds to CUE time format (MM:SS:FF).

    Rounds to the nearest CD frame (1/75th of a second).
    """
    total_frames = round(total_seconds * 75)
    minutes = total_frames // (75 * 60)
    remaining_frames = total_frames % (75 * 60)
    seconds = remaining_frames // 75
    frames = remaining_frames % 75
    return f"{minutes:02d}:{seconds:02d}:{frames:02d}"


def ms_to_timestamp(ms: int) -> str:
    """Convert milliseconds to HH:MM:SS.mmm format (for MP4Box)."""
    hours = ms // 3600000
    ms %= 3600000
    minutes = ms // 60000
    ms %= 60000
    seconds = ms // 1000
    ms %= 1000
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{ms:03d}"
