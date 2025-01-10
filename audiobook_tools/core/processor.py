"""Core functionality for processing audiobooks.

This module provides the main processing logic for converting audiobooks from FLAC+CUE
format to M4B audiobooks with chapters. It handles the complete workflow including:

1. Finding and merging FLAC files
2. Processing CUE sheets for chapter information
3. Converting audio to AAC format
4. Creating M4B files with chapters

Example:
    ```python
    from pathlib import Path
    from audiobook_tools.core.processor import (
        AudiobookProcessor,
        ProcessingOptions,
        AudiobookMetadata,
    )

    metadata = AudiobookMetadata(
        title="My Audiobook",
        artist="Author Name"
    )
    
    options = ProcessingOptions(
        input_dir=Path("./audiobook"),
        output_dir=Path("./out"),
        output_format="m4b-ffmpeg",
        metadata=metadata
    )
    
    processor = AudiobookProcessor(options)
    output_file = processor.process()
    ```

The processor supports multiple output formats:
- m4b-ffmpeg: M4B file with chapters using FFmpeg (recommended)
- m4b-mp4box: M4B file with chapters using MP4Box
- aac: AAC audio file without chapters

For spoken word audio, the processor uses optimized encoding settings:
- AAC codec for good quality at low bitrates
- Default 64k bitrate (can be customized)
- Mono output (can be customized)
"""

import logging
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from ..common import AudiobookMetadata
from ..utils.audio import (
    AudioConfig,
    AudioProcessingError,
    convert_to_aac,
    create_m4b,
    create_m4b_mp4box,
    merge_flac_files,
    merge_mp3_files,
)
from .cue import CueProcessor

logger = logging.getLogger(__name__)


@dataclass
class ProcessingOptions:
    """Options for audiobook processing."""

    input_dir: Path
    output_dir: Path
    output_format: str = "m4b-ffmpeg"  # One of: m4b-ffmpeg, m4b-mp4box, aac
    audio_config: AudioConfig = field(default_factory=AudioConfig)
    metadata: AudiobookMetadata = field(default_factory=AudiobookMetadata)
    dry_run: bool = False
    resume: bool = False  # Whether to resume from existing intermediate files


class AudiobookProcessor:
    """Handles the complete audiobook processing workflow."""

    def __init__(self, options: ProcessingOptions):
        """Initialize the audiobook processor.

        Args:
            options: Processing options
        """
        self.options = options
        self.options.output_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _extract_track_number(filename: Path) -> int:
        """Extract track number from MP3 filename.

        Args:
            filename: Path to MP3 file

        Returns:
            Track number as integer, or 0 if not found
        """
        # Look for CD and track number pattern
        match = re.search(r"CD\d+ - (\d+) -", filename.stem)
        if not match:
            return 0
        return int(match.group(1))

    @staticmethod
    def _extract_cd_number(filename: Path) -> int:
        """Extract CD number from MP3 filename.

        Args:
            filename: Path to MP3 file

        Returns:
            CD number as integer, or 0 if not found
        """
        match = re.search(r"CD(\d+)", filename.stem)
        if not match:
            return 0
        return int(match.group(1))

    def find_audio_files(self) -> List[Path]:
        """Find all audio files in the input directory.

        Returns:
            List of paths to audio files, sorted by CD/track number

        Raises:
            AudioProcessingError: If no audio files are found
        """
        # Find all FLAC files that match CD patterns
        flac_files = sorted(
            [
                f
                for f in self.options.input_dir.rglob("*.flac")
                if "CD" in f.stem or "cd" in f.stem
            ],
            key=lambda p: int(
                "".join(filter(str.isdigit, p.stem))
            ),  # Sort by CD number
        )

        if flac_files:
            return flac_files

        # If no FLAC files found, look for MP3 files recursively
        mp3_files = list(
            f
            for f in self.options.input_dir.rglob("*.mp3")
            # Only include files that match our chapter pattern
            if re.search(r"(?:CD\d+.*?)? - \d+ - Chapter \d+.*?\.mp3$", str(f))
        )

        # Determine if we have a CD-based structure
        has_cd_structure = any("CD" in f.stem for f in mp3_files)

        # Sort based on structure
        if has_cd_structure:
            mp3_files = sorted(
                mp3_files,
                key=lambda p: (
                    self._extract_cd_number(p),
                    self._extract_track_number(p),
                ),
            )
        else:
            mp3_files = sorted(
                mp3_files, key=lambda p: int(re.search(r" - (\d+) -", str(p)).group(1))
            )

        if not mp3_files:
            raise AudioProcessingError(
                f"No valid FLAC or MP3 files found in {self.options.input_dir}"
            )

        return mp3_files

    @staticmethod
    def _get_mp3_duration(mp3_file: Path) -> int:
        """Get duration of MP3 file in seconds.

        Args:
            mp3_file: Path to MP3 file

        Returns:
            Duration in seconds, or 0 if duration cannot be determined
        """
        cmd = ["ffmpeg", "-i", str(mp3_file)]
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        duration_match = re.search(r"Duration: (\d{2}):(\d{2}):(\d{2})", result.stderr)
        if duration_match:
            hours, minutes, seconds = map(int, duration_match.groups())
            return hours * 3600 + minutes * 60 + seconds
        return 0

    @staticmethod
    def _format_timestamp(seconds: int) -> str:
        """Format seconds as HH:MM:SS.

        Args:
            seconds: Number of seconds

        Returns:
            Formatted timestamp
        """
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"

    def extract_chapters_from_filenames(self, mp3_files: List[Path]) -> Path:
        """Extract chapter information from MP3 filenames.

        Args:
            mp3_files: List of paths to MP3 files

        Returns:
            Path to the generated chapters file

        Raises:
            AudioProcessingError: If chapter information cannot be extracted
        """
        chapters_file = self.options.output_dir / "chapters.txt"
        pattern = re.compile(r".*? - \d+ - (Chapter \d+.*?)\.mp3$")

        # Track chapter occurrences for suffixes
        chapter_counts = {}  # Dict to track how many times we've seen each chapter
        chapters = []  # List to store chapter info in order

        current_time = 0
        for mp3_file in mp3_files:
            match = pattern.search(str(mp3_file))
            if not match:
                logger.warning("Skipping malformed file: %s", mp3_file)
                continue

            chapter_title = match.group(1)
            duration = self._get_mp3_duration(mp3_file)
            if duration <= 0:
                continue

            # Special case for "Introduction" - don't add a suffix
            if "Introduction" in chapter_title:
                display_title = chapter_title
            else:
                # Add suffix starting from first occurrence
                if chapter_title not in chapter_counts:
                    chapter_counts[chapter_title] = 0
                chapter_counts[chapter_title] += 1
                display_title = f"{chapter_title} ({chapter_counts[chapter_title]})"

            chapters.append(
                {
                    "title": display_title,
                    "start": current_time,
                    "end": current_time + duration,
                }
            )
            current_time += duration

        # Write chapters file
        with open(chapters_file, "w", encoding="utf-8") as f:
            f.write(";FFMETADATA1\n")  # FFmpeg metadata header

            for i, chapter in enumerate(chapters):
                f.write("[CHAPTER]\n")
                f.write("TIMEBASE=1/1\n")
                f.write(f"START={chapter['start']}\n")
                f.write(f"END={chapter['end']}\n")
                # Don't add newline after last chapter
                if i < len(chapters) - 1:
                    f.write(f"title={chapter['title']}\n")
                else:
                    f.write(f"title={chapter['title']}")

        return chapters_file

    def process(self) -> Path:
        """Process the audiobook files.

        This method:
        1. Finds audio files (FLAC or MP3)
        2. Processes chapters (from CUE sheets or filenames)
        3. Converts to AAC (if needed)
        4. Creates final M4B with chapters

        Returns:
            Path to the final audiobook file

        Raises:
            AudioProcessingError: If there are issues processing the audiobook
        """
        logger.info("Starting audiobook processing...")

        # Find audio files
        audio_files = self.find_audio_files()
        is_mp3 = audio_files[0].suffix.lower() == ".mp3"
        logger.info("Found %d %s files", len(audio_files), "MP3" if is_mp3 else "FLAC")

        # Show files that will be processed
        for i, file in enumerate(audio_files, 1):
            logger.info("%d. %s", i, file)

        if self.options.dry_run:
            logger.info("Dry run complete. No files were processed.")
            return Path()

        # Process files based on type
        if is_mp3:
            # For MP3 files, merge them and extract chapters from filenames
            combined_audio = self.options.output_dir / "combined.mp3"
            if not (self.options.resume and combined_audio.exists()):
                logger.info("Merging MP3 files...")
                merge_mp3_files(audio_files, combined_audio)
            else:
                logger.info("Using existing combined MP3 file: %s", combined_audio)

            # Extract chapters from filenames
            logger.info("Processing chapter information from filenames...")
            chapters_file = self.extract_chapters_from_filenames(audio_files)
        else:
            # For FLAC files, use existing merge and CUE processing
            combined_audio = self.options.output_dir / "combined.flac"
            if not (self.options.resume and combined_audio.exists()):
                logger.info("Merging FLAC files...")
                merge_flac_files(audio_files, combined_audio)
            else:
                logger.info("Using existing combined FLAC file: %s", combined_audio)

            # Process CUE sheets
            logger.info("Processing CUE sheets...")
            cue_processor = CueProcessor(
                self.options.input_dir, self.options.output_dir
            )
            chapters_file = cue_processor.process_directory()

        # Convert to AAC if needed
        if self.options.output_format != "aac":
            logger.info("Converting to AAC...")
            aac_file = self.options.output_dir / "audiobook.aac"
            if not (self.options.resume and aac_file.exists()):
                convert_to_aac(
                    combined_audio, aac_file, config=self.options.audio_config
                )
            else:
                logger.info("Using existing AAC file: %s", aac_file)

            # Create M4B with chapters
            logger.info("Creating %s...", self.options.output_format)
            output_file = self.options.output_dir / "audiobook.m4b"

            if self.options.output_format == "m4b-ffmpeg":
                create_m4b(
                    aac_file,
                    output_file,
                    chapters_file=chapters_file,
                    metadata=self.options.metadata,
                )
                return output_file

            # m4b-mp4box
            create_m4b_mp4box(aac_file, output_file, chapters_file=chapters_file)
            return output_file

        # Just convert to AAC
        logger.info("Converting to AAC...")
        output_file = self.options.output_dir / "audiobook.aac"
        convert_to_aac(combined_audio, output_file, config=self.options.audio_config)
        return output_file
