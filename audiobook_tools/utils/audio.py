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
import subprocess
from pathlib import Path
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

class AudioProcessingError(Exception):
    """Base exception for audio processing errors."""
    pass

def merge_flac_files(input_files: List[Path], output_file: Path) -> None:
    """Merge multiple FLAC files into a single file using sox.
    
    Args:
        input_files: List of paths to input FLAC files
        output_file: Path where the merged file will be written
        
    Raises:
        AudioProcessingError: If there are issues merging the files
    """
    try:
        cmd = ['sox'] + [str(f) for f in input_files] + [str(output_file)]
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        raise AudioProcessingError(f"Failed to merge FLAC files: {e.stderr}")

def convert_to_aac(
    input_file: Path,
    output_file: Path,
    bitrate: str = "256k",
    channels: int = 2,
    sample_rate: int = 44100
) -> None:
    """Convert an audio file to AAC format using ffmpeg.
    
    Args:
        input_file: Path to input audio file
        output_file: Path where the AAC file will be written
        bitrate: Target bitrate (default: "256k")
        channels: Number of audio channels (default: 2)
        sample_rate: Sample rate in Hz (default: 44100)
        
    Raises:
        AudioProcessingError: If there are issues converting the file
    """
    try:
        cmd = [
            'ffmpeg',
            '-i', str(input_file),
            '-c:a', 'aac',
            '-b:a', bitrate,
            '-ac', str(channels),
            '-ar', str(sample_rate),
            '-y',  # Overwrite output file if it exists
            str(output_file)
        ]
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        raise AudioProcessingError(f"Failed to convert to AAC: {e.stderr}")

def create_m4b(
    input_file: Path,
    output_file: Path,
    chapters_file: Optional[Path] = None,
    title: Optional[str] = None,
    artist: Optional[str] = None,
    cover_art: Optional[Path] = None
) -> None:
    """Create an M4B audiobook file with metadata using ffmpeg.
    
    Args:
        input_file: Path to input audio file (should be AAC)
        output_file: Path where the M4B file will be written
        chapters_file: Optional path to FFmpeg metadata file with chapters
        title: Optional audiobook title
        artist: Optional audiobook artist/author
        cover_art: Optional path to cover art image
        
    Raises:
        AudioProcessingError: If there are issues creating the M4B file
    """
    try:
        cmd = ['ffmpeg', '-i', str(input_file)]
        
        # Add metadata if provided
        if title:
            cmd.extend(['-metadata', f'title={title}'])
        if artist:
            cmd.extend(['-metadata', f'artist={artist}'])
            
        # Add cover art if provided
        if cover_art:
            cmd.extend(['-i', str(cover_art), '-map', '0:a', '-map', '1:v'])
            
        # Add chapters if provided
        if chapters_file:
            cmd.extend(['-i', str(chapters_file), '-map_metadata', '1'])
            
        # Output options
        cmd.extend([
            '-c:a', 'copy',  # Copy audio stream without re-encoding
            '-c:v', 'copy' if cover_art else None,  # Copy video (cover art) if present
            '-f', 'mp4',  # Force MP4 container
            '-y',  # Overwrite output file if it exists
            str(output_file)
        ])
        
        # Remove None values from command
        cmd = [arg for arg in cmd if arg is not None]
        
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        raise AudioProcessingError(f"Failed to create M4B file: {e.stderr}")

def create_m4b_mp4box(
    input_file: Path,
    output_file: Path,
    chapters_file: Optional[Path] = None
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
        cmd = ['MP4Box', '-add', str(input_file)]
        
        if chapters_file:
            cmd.extend(['-chap', str(chapters_file)])
            
        cmd.append(str(output_file))
        
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        raise AudioProcessingError(f"Failed to create M4B file with MP4Box: {e.stderr}")

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
            'ffmpeg',
            '-i', str(input_file),
            '-an',  # Disable audio
            '-vcodec', 'copy',  # Copy video stream (cover art)
            '-y',
            str(output_file)
        ]
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        raise AudioProcessingError(f"Failed to extract cover art: {e.stderr}") 