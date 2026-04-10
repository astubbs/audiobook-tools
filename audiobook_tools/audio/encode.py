"""Audio encoding utilities."""

import subprocess
from pathlib import Path

from audiobook_tools.utils.external import require_tool


def encode_to_aac(
    input_path: Path,
    output_path: Path,
    bitrate: str = "64k",
) -> None:
    """Encode an audio file to AAC, optimized for spoken word.

    Args:
        input_path: Path to the input audio file (FLAC, WAV, MP3, etc.).
        output_path: Where to write the AAC file.
        bitrate: Audio bitrate (default 64k for spoken word).
    """
    require_tool("ffmpeg")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg", "-y",
        "-i", str(input_path),
        "-c:a", "aac",
        "-b:a", bitrate,
        "-movflags", "+faststart",
        str(output_path),
    ]
    print(f"Encoding to AAC ({bitrate})...")
    subprocess.run(cmd, check=True)
    print(f"AAC file created: {output_path}")
