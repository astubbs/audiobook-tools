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
    from audiobook_tools.core.processor import AudiobookProcessor, ProcessingOptions

    options = ProcessingOptions(
        input_dir=Path("./audiobook"),
        output_dir=Path("./out"),
        output_format="m4b-ffmpeg",
        title="My Audiobook",
        artist="Author Name"
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
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from ..utils.audio import (
    AudioConfig,
    AudioProcessingError,
    convert_to_aac,
    create_m4b,
    create_m4b_mp4box,
    merge_flac_files,
)
from .cue import CueProcessor

logger = logging.getLogger(__name__)


@dataclass
class ProcessingOptions:
    """Options for audiobook processing."""

    input_dir: Path
    output_dir: Path
    output_format: str = "m4b-ffmpeg"  # One of: m4b-ffmpeg, m4b-mp4box, aac
    audio_config: AudioConfig = AudioConfig()  # Use AudioConfig for audio settings
    title: Optional[str] = None
    artist: Optional[str] = None
    cover_art: Optional[Path] = None
    dry_run: bool = False


class AudiobookProcessor:
    """Handles the complete audiobook processing workflow."""

    def __init__(self, options: ProcessingOptions):
        """Initialize the audiobook processor.

        Args:
            options: Processing options
        """
        self.options = options
        self.options.output_dir.mkdir(parents=True, exist_ok=True)

    def find_flac_files(self) -> List[Path]:
        """Find all FLAC files in the input directory.

        Returns:
            List of paths to FLAC files, sorted by CD number

        Raises:
            AudioProcessingError: If no FLAC files are found
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

        if not flac_files:
            raise AudioProcessingError(
                f"No FLAC files found in {self.options.input_dir}"
            )

        return flac_files

    def process(self) -> Path:
        """Process the audiobook files.

        This method:
        1. Finds and merges FLAC files
        2. Processes CUE sheets
        3. Converts to AAC (if needed)
        4. Creates final M4B with chapters

        Returns:
            Path to the final audiobook file

        Raises:
            AudioProcessingError: If there are issues processing the audiobook
        """
        logger.info("Starting audiobook processing...")

        # Find FLAC files
        flac_files = self.find_flac_files()
        logger.info("Found %d FLAC files", len(flac_files))

        # Show files that will be processed
        for i, file in enumerate(flac_files, 1):
            logger.info("%d. %s", i, file)

        if self.options.dry_run:
            logger.info("Dry run complete. No files were processed.")
            return Path()

        # Merge FLAC files
        combined_flac = self.options.output_dir / "combined.flac"
        logger.info("Merging FLAC files...")
        merge_flac_files(flac_files, combined_flac)

        # Process CUE sheets
        logger.info("Processing CUE sheets...")
        cue_processor = CueProcessor(self.options.input_dir, self.options.output_dir)
        chapters_file = cue_processor.process_directory()

        # Convert to AAC if needed
        if self.options.output_format != "aac":
            logger.info("Converting to AAC...")
            aac_file = self.options.output_dir / "audiobook.aac"
            convert_to_aac(combined_flac, aac_file, config=self.options.audio_config)

            # Create M4B with chapters
            logger.info("Creating %s...", self.options.output_format)
            output_file = self.options.output_dir / "audiobook.m4b"

            if self.options.output_format == "m4b-ffmpeg":
                create_m4b(
                    aac_file,
                    output_file,
                    chapters_file=chapters_file,
                    title=self.options.title,
                    artist=self.options.artist,
                    cover_art=self.options.cover_art,
                )
                return output_file

            # m4b-mp4box
            create_m4b_mp4box(aac_file, output_file, chapters_file=chapters_file)
            return output_file

        # Just convert to AAC
        logger.info("Converting to AAC...")
        output_file = self.options.output_dir / "audiobook.aac"
        convert_to_aac(combined_flac, output_file, config=self.options.audio_config)
        return output_file
