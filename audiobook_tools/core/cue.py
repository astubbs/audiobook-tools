"""Core functionality for CUE sheet processing."""

import json
import logging
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class CueProcessingError(Exception):
    """Base exception for CUE processing errors."""


class InvalidCueFormatError(CueProcessingError):
    """Raised when CUE file format is invalid."""


class AudioFileError(CueProcessingError):
    """Raised when there are issues with audio file processing."""


@dataclass
class Track:
    """Represents a track in a CUE sheet."""

    number: int
    title: Optional[str]
    performer: Optional[str]
    index: Dict[int, str]  # index number -> timestamp


@dataclass
class CueSheet:
    """Represents a parsed CUE sheet."""

    file_path: Path
    audio_file: str
    tracks: List[Track]


class CueProcessor:
    """Handles CUE sheet processing and combining."""

    def __init__(self, base_dir: Path, output_dir: Path):
        """Initialize the CUE processor.

        Args:
            base_dir: Base directory containing audiobook files
            output_dir: Directory for output files
        """
        self.base_dir = Path(base_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def time_to_seconds(time_str: str) -> float:
        """Convert a time string in MM:SS:FF format to seconds.

        Args:
            time_str: String in format "MM:SS:FF" where FF is frames (75 frames per second)

        Returns:
            Float representing the time in seconds

        Raises:
            InvalidCueFormatError: If time string format is invalid
        """
        try:
            if not re.match(r"^\d{2}:\d{2}:\d{2}$", time_str):
                raise InvalidCueFormatError(f"Invalid time format: {time_str}")

            minutes, seconds, frames = map(int, time_str.split(":"))
            if seconds >= 60 or frames >= 75:
                raise InvalidCueFormatError(f"Invalid time values in: {time_str}")

            return minutes * 60 + seconds + frames / 75.0
        except ValueError as e:
            raise InvalidCueFormatError(f"Error parsing time: {time_str}") from e

    @staticmethod
    def seconds_to_time(seconds: float) -> str:
        """Convert seconds to a time string in MM:SS:FF format.

        Args:
            seconds: Float representing time in seconds

        Returns:
            String in format "MM:SS:FF" where FF is frames (75 frames per second)
        """
        total_frames = round(seconds * 75)
        minutes = total_frames // (75 * 60)
        remaining_frames = total_frames % (75 * 60)
        seconds = remaining_frames // 75
        frames = remaining_frames % 75
        return f"{minutes:02d}:{seconds:02d}:{frames:02d}"

    def get_audio_length(self, audio_file_path: Path) -> float:
        """Get the duration of an audio file in seconds using ffprobe.

        Args:
            audio_file_path: Path to the audio file

        Returns:
            Float representing the duration in seconds

        Raises:
            AudioFileError: If there are issues reading the audio file
        """
        cmd = [
            "ffprobe",
            "-v",
            "quiet",
            "-print_format",
            "json",
            "-show_format",
            str(audio_file_path),
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            data = json.loads(result.stdout)
            return float(data["format"]["duration"])
        except subprocess.CalledProcessError as e:
            raise AudioFileError(f"Failed to read audio file: {audio_file_path}") from e
        except (json.JSONDecodeError, KeyError) as e:
            raise AudioFileError(
                f"Invalid ffprobe output for: {audio_file_path}"
            ) from e

    def parse_cue_file(self, cue_path: Path) -> CueSheet:
        """Parse a CUE file into a structured format.

        Args:
            cue_path: Path to the CUE file

        Returns:
            CueSheet object representing the parsed CUE file

        Raises:
            InvalidCueFormatError: If CUE file format is invalid
        """
        try:
            with open(cue_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
        except UnicodeDecodeError as e:
            raise InvalidCueFormatError(
                f"Invalid encoding in CUE file: {cue_path}"
            ) from e

        # Parse FILE directive
        file_match = next(
            (line for line in lines if line.strip().startswith("FILE")), None
        )
        if not file_match:
            raise InvalidCueFormatError(f"No FILE directive found in: {cue_path}")

        audio_file = re.search(r'FILE\s+"([^"]+)"', file_match).group(1)

        # Parse tracks
        tracks = []
        current_track = None

        for line in lines:
            line = line.strip()

            if line.startswith("TRACK"):
                if current_track:
                    tracks.append(current_track)
                track_num = int(re.search(r"TRACK\s+(\d+)\s+AUDIO", line).group(1))
                current_track = Track(
                    number=track_num, title=None, performer=None, index={}
                )

            elif current_track:
                if line.startswith("TITLE"):
                    current_track.title = re.search(r'TITLE\s+"([^"]+)"', line).group(1)
                elif line.startswith("PERFORMER"):
                    current_track.performer = re.search(
                        r'PERFORMER\s+"([^"]+)"', line
                    ).group(1)
                elif line.startswith("INDEX"):
                    match = re.search(r"INDEX\s+(\d+)\s+(\d{2}:\d{2}:\d{2})", line)
                    if match:
                        index_num = int(match.group(1))
                        current_track.index[index_num] = match.group(2)

        if current_track:
            tracks.append(current_track)

        return CueSheet(file_path=cue_path, audio_file=audio_file, tracks=tracks)

    def combine_cue_sheets(self, cue_files: List[Path]) -> str:
        """Combine multiple CUE sheets into a single CUE file.

        Args:
            cue_files: List of paths to CUE files

        Returns:
            String containing the combined CUE content

        Raises:
            CueProcessingError: If there are issues processing CUE files
        """
        combined_content = []
        track_number = 1

        for i, cue_path in enumerate(cue_files):
            logger.info("Processing CUE file: %s", cue_path)
            cue_sheet = self.parse_cue_file(cue_path)

            # Calculate cumulative duration for time offsets
            cumulative_duration = sum(
                self.get_audio_length(cue.file_path.parent / cue.audio_file)
                for cue in map(self.parse_cue_file, cue_files[:i])
            )

            # Add FILE directive
            combined_content.append(f'FILE "{cue_sheet.audio_file}" WAVE')

            # Process tracks
            for track in cue_sheet.tracks:
                combined_content.append(f"  TRACK {track_number:02d} AUDIO")
                if track.title:
                    combined_content.append(f'    TITLE "{track.title}"')
                if track.performer:
                    combined_content.append(f'    PERFORMER "{track.performer}"')

                # Adjust timestamps for each index
                for index_num, timestamp in track.index.items():
                    time_seconds = self.time_to_seconds(timestamp) + cumulative_duration
                    adjusted_time = self.seconds_to_time(time_seconds)
                    combined_content.append(
                        f"    INDEX {index_num:02d} {adjusted_time}"
                    )

                track_number += 1

        return "\n".join(combined_content)

    def process_directory(self) -> Path:
        """Process the base directory and combine all CUE files.

        Returns:
            Path to the combined CUE file

        Raises:
            CueProcessingError: If there are issues processing the directory
        """
        # Find all CUE files
        cue_files = sorted(
            self.base_dir.rglob("*.cue"),
            key=lambda p: int(re.search(r"CD(\d+)", str(p)).group(1)),
        )

        if not cue_files:
            raise CueProcessingError(f"No CUE files found in: {self.base_dir}")

        # Combine CUE sheets
        combined_content = self.combine_cue_sheets(cue_files)

        # Write combined CUE file
        output_file = self.output_dir / "combined.cue"
        output_file.write_text(combined_content, encoding="utf-8")

        return output_file
