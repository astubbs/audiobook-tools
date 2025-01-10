"""Utility functions for audio file operations.

This module provides low-level audio processing functions that wrap common
command-line tools (FFmpeg, sox, MP4Box) in a Pythonic interface. It handles:

1. FLAC Operations:
   - Merging multiple FLAC files
   - Reading audio file durations

2. Format Conversion:
   - Converting FLAC to AAC
   - Creating M4B files with chapters
   - Extracting cover art

Example:
    ```python
    from pathlib import Path
    from audiobook_tools.utils.audio import merge_flac_files, convert_to_aac

    # Merge FLAC files
    flac_files = [Path("cd1.flac"), Path("cd2.flac")]
    merge_flac_files(flac_files, Path("combined.flac"))

    # Convert to AAC
    convert_to_aac(
        Path("combined.flac"),
        Path("audiobook.aac"),
        bitrate="64k",
        channels=1
    )
    ```

Requirements:
    This module requires several external tools to be installed:
    - FFmpeg: For audio conversion and M4B creation
    - sox: For lossless FLAC merging
    - MP4Box (optional): Alternative method for M4B creation

Error Handling:
    All functions raise AudioProcessingError with detailed error messages
    when external tools fail or return unexpected results.
"""

import logging
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from ..common import AudiobookMetadata

logger = logging.getLogger(__name__)


class AudioProcessingError(Exception):
    """Base exception for audio processing errors."""


@dataclass
class AudioConfig:
    """Configuration for audio conversion."""

    bitrate: str = "64k"
    channels: int = 1  # Mono for spoken word
    sample_rate: int = 44100


def merge_flac_files(input_files: List[Path], output_file: Path) -> None:
    """Merge multiple FLAC files into a single file using sox.

    Args:
        input_files: List of paths to input FLAC files
        output_file: Path where the merged file will be written

    Raises:
        AudioProcessingError: If there are issues merging the files
    """
    try:
        cmd = ["sox"] + [str(f) for f in input_files] + [str(output_file)]
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        raise AudioProcessingError(f"Failed to merge FLAC files: {e.stderr}") from e


def convert_to_aac(
    input_file: Path,
    output_file: Path,
    config: AudioConfig = AudioConfig(),
) -> None:
    """Convert an audio file to AAC format using ffmpeg.

    Args:
        input_file: Path to input audio file
        output_file: Path where the AAC file will be written
        config: Audio configuration settings

    Raises:
        AudioProcessingError: If there are issues converting the file
    """
    try:
        cmd = [
            "ffmpeg",
            "-stats",  # Show progress statistics
            "-i",
            str(input_file),
            "-c:a",
            "aac",
            "-b:a",
            config.bitrate,
            "-ac",
            str(config.channels),
            "-ar",
            str(config.sample_rate),
            "-y",
            str(output_file),
        ]
        # Run without capturing stdout to show progress
        result = subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.PIPE,  # Still capture stdout for error handling
            stderr=None,  # Let stderr through for progress
            text=True,
        )
    except subprocess.CalledProcessError as e:
        raise AudioProcessingError(f"Failed to convert to AAC: {e.stderr if hasattr(e, 'stderr') else str(e)}") from e


def create_m4b(
    input_file: Path,
    output_file: Path,
    chapters_file: Optional[Path] = None,
    metadata: Optional[AudiobookMetadata] = None,
) -> None:
    """Create an M4B audiobook file using ffmpeg.

    Args:
        input_file: Path to input audio file (should be AAC)
        output_file: Path where the M4B file will be written
        chapters_file: Optional path to ffmpeg chapters file
        metadata: Optional metadata to add to the M4B file

    Raises:
        AudioProcessingError: If there are issues creating the M4B file
    """
    try:
        cmd = ["ffmpeg", "-stats"]  # Show progress statistics

        # Add input file
        cmd.extend(["-i", str(input_file)])

        # Add chapters if provided
        if chapters_file:
            cmd.extend(["-i", str(chapters_file)])  # Add chapters file as second input
            cmd.extend(["-map_metadata", "1"])  # Map metadata from second input

        # Add metadata if provided
        if metadata:
            if metadata.title:
                cmd.extend(["-metadata", f"title={metadata.title}"])
            if metadata.artist:
                cmd.extend(["-metadata", f"artist={metadata.artist}"])
            if metadata.cover_art:
                cmd.extend(["-i", str(metadata.cover_art), "-map", "2"])

        # Map audio stream and set output options
        cmd.extend(["-map", "0:a"])  # Map audio from first input
        cmd.extend(["-c", "copy", "-y", str(output_file)])

        # Run without capturing stderr to show progress
        result = subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.PIPE,  # Still capture stdout for error handling
            stderr=None,  # Let stderr through for progress
            text=True,
        )
    except subprocess.CalledProcessError as e:
        raise AudioProcessingError(f"Failed to create M4B file: {e.stderr if hasattr(e, 'stderr') else str(e)}") from e


def create_m4b_mp4box(
    input_file: Path, output_file: Path, chapters_file: Optional[Path] = None
) -> None:
    """Create an M4B audiobook file using MP4Box.

    Args:
        input_file: Path to input audio file (should be AAC)
        output_file: Path where the M4B file will be written
        chapters_file: Optional path to MP4Box chapters file

    Raises:
        AudioProcessingError: If there are issues creating the M4B file
    """
    try:
        cmd = ["MP4Box", "-add", str(input_file)]

        if chapters_file:
            cmd.extend(["-chap", str(chapters_file)])

        cmd.append(str(output_file))

        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        raise AudioProcessingError(
            f"Failed to create M4B file with MP4Box: {e.stderr}"
        ) from e


def extract_cover_art(input_file: Path, output_file: Path) -> None:
    """Extract cover art from an audio file using ffmpeg.

    Args:
        input_file: Path to input audio file
        output_file: Path where the cover art will be written

    Raises:
        AudioProcessingError: If there are issues extracting the cover art
    """
    try:
        cmd = [
            "ffmpeg",
            "-i",
            str(input_file),
            "-an",  # Disable audio
            "-vcodec",
            "copy",  # Copy video stream (cover art)
            "-y",
            str(output_file),
        ]
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        raise AudioProcessingError(f"Failed to extract cover art: {e.stderr}") from e


def merge_mp3_files(input_files: List[Path], output_file: Path) -> None:
    """Merge multiple MP3 files into a single file using ffmpeg.

    Args:
        input_files: List of paths to input MP3 files
        output_file: Path where the merged file will be written

    Raises:
        AudioProcessingError: If there are issues merging the files
    """
    try:
        # Create a concat file listing all inputs
        concat_file = output_file.parent / "concat.txt"
        with open(concat_file, "w", encoding="utf-8") as f:
            for input_file in input_files:
                f.write(f"file '{input_file.absolute()}'\n")

        # Merge files using ffmpeg concat demuxer
        cmd = [
            "ffmpeg",
            "-stats",  # Show progress statistics
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_file),
            "-c", "copy",
            "-y",
            str(output_file)
        ]

        # Run without capturing stderr to show progress
        result = subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.PIPE,  # Still capture stdout for error handling
            stderr=None,  # Let stderr through for progress
            text=True,
        )

        # Clean up concat file
        concat_file.unlink()
    except subprocess.CalledProcessError as e:
        raise AudioProcessingError(f"Failed to merge MP3 files: {e.stderr if hasattr(e, 'stderr') else str(e)}") from e
