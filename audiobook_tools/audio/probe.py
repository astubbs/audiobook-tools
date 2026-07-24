"""FFprobe wrapper for querying audio file properties."""

import json
import subprocess
from pathlib import Path


def get_duration_seconds(audio_file: str | Path) -> float:
    """Get the duration of an audio file in seconds using ffprobe."""
    cmd = [
        "ffprobe",
        "-v",
        "quiet",
        "-print_format",
        "json",
        "-show_format",
        str(audio_file),
    ]
    result = subprocess.run(
        cmd, capture_output=True, text=True, check=True, stdin=subprocess.DEVNULL
    )
    data = json.loads(result.stdout)
    return float(data["format"]["duration"])


def get_duration_ms(audio_file: str | Path) -> int:
    """Get the duration of an audio file in milliseconds using ffprobe."""
    return int(get_duration_seconds(audio_file) * 1000)
