"""M4B audiobook creation."""

import subprocess
from pathlib import Path

from audiobook_tools.utils.external import require_tool


def create_m4b_ffmpeg(
    audio_path: Path,
    chapters_path: Path,
    output_path: Path,
    title: str | None = None,
    artist: str | None = None,
    cover_path: Path | None = None,
) -> None:
    """Create an M4B audiobook using FFmpeg.

    Args:
        audio_path: Path to the AAC audio file.
        chapters_path: Path to the FFMETADATA1 chapters file.
        output_path: Where to write the M4B file.
        title: Optional audiobook title metadata.
        artist: Optional artist/author metadata.
        cover_path: Optional cover art image.
    """
    require_tool("ffmpeg")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(audio_path),
        "-i",
        str(chapters_path),
    ]

    if cover_path:
        cmd.extend(["-i", str(cover_path)])

    cmd.extend(["-map_metadata", "1"])

    if cover_path:
        cmd.extend(
            [
                "-map",
                "0:a",
                "-map",
                "2:v",
                "-disposition:v:0",
                "attached_pic",
            ]
        )

    cmd.extend(["-c:a", "copy"])

    if title:
        cmd.extend(["-metadata", f"title={title}"])
    if artist:
        cmd.extend(["-metadata", f"artist={artist}"])

    cmd.extend(["-movflags", "+faststart", str(output_path)])

    print("Creating M4B with FFmpeg...")
    subprocess.run(cmd, check=True)
    print(f"M4B file created: {output_path}")


def create_m4b_mp4box(
    audio_path: Path,
    chapters_path: Path,
    output_path: Path,
) -> None:
    """Create an M4B audiobook using MP4Box.

    Args:
        audio_path: Path to the AAC audio file.
        chapters_path: Path to the MP4Box chapters file.
        output_path: Where to write the M4B file.
    """
    require_tool("MP4Box")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "MP4Box",
        "-add",
        str(audio_path),
        "-chap",
        str(chapters_path),
        str(output_path),
    ]
    print("Creating M4B with MP4Box...")
    subprocess.run(cmd, check=True)
    print(f"M4B file created: {output_path}")
