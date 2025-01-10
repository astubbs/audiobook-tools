"""Tests for processing MP3 files with chapter information in filenames."""

import re
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from audiobook_tools.common import AudiobookMetadata
from audiobook_tools.core.processor import AudiobookProcessor, ProcessingOptions
from audiobook_tools.utils.audio import AudioConfig


@pytest.fixture
def sample_mp3_files(tmp_path: Path) -> Path:  # pylint: disable=redefined-outer-name
    """Create a sample directory with MP3 files that have chapter information in filenames."""
    book_dir = tmp_path / "Test Author - Test Book (Audio Book)"
    book_dir.mkdir()

    # Create sample MP3 files
    filenames = [
        "Test Author - Test Book (Audio Book) - 01 - Chapter 1 - Introduction.mp3",
        "Test Author - Test Book (Audio Book) - 02 - Chapter 1.mp3",
        "Test Author - Test Book (Audio Book) - 03 - Chapter 2.mp3",
        "Test Author - Test Book (Audio Book) - 04 - Chapter 2.mp3",
    ]

    for filename in filenames:
        (book_dir / filename).touch()

    return book_dir


def test_detect_mp3_chapters(
    sample_mp3_files: Path,
):  # pylint: disable=redefined-outer-name
    """Test that we can detect MP3 files and extract chapter information."""
    mp3_files = sorted(sample_mp3_files.glob("*.mp3"))
    assert len(mp3_files) == 4

    # Test filename pattern matching
    pattern = re.compile(r".*? - (\d+) - (Chapter \d+.*?)\.mp3$")

    # Check first file (with introduction)
    match = pattern.search(str(mp3_files[0]))
    assert match is not None
    assert match.group(1) == "01"
    assert match.group(2) == "Chapter 1 - Introduction"

    # Check second file (regular chapter)
    match = pattern.search(str(mp3_files[1]))
    assert match is not None
    assert match.group(1) == "02"
    assert match.group(2) == "Chapter 1"


def test_no_cue_files(sample_mp3_files: Path):  # pylint: disable=redefined-outer-name
    """Test that the directory has no CUE files but is still valid."""
    cue_files = list(sample_mp3_files.glob("*.cue"))
    assert len(cue_files) == 0

    flac_files = list(sample_mp3_files.glob("*.flac"))
    assert len(flac_files) == 0

    mp3_files = list(sample_mp3_files.glob("*.mp3"))
    assert len(mp3_files) > 0


@patch("audiobook_tools.utils.audio.subprocess.run")
def test_process_mp3_files(
    mock_run: Mock, sample_mp3_files: Path, tmp_path: Path
):  # pylint: disable=redefined-outer-name
    """Test processing MP3 files into M4B with chapters."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    metadata = AudiobookMetadata(
        title="Test Book", artist="Test Author", cover_art=None
    )

    audio_config = AudioConfig(bitrate="64k")

    # Create processing options
    options = ProcessingOptions(
        input_dir=sample_mp3_files,
        output_dir=output_dir,
        output_format="m4b-ffmpeg",
        metadata=metadata,
        audio_config=audio_config,
        dry_run=False,
    )

    # Mock ffmpeg duration query
    def mock_ffmpeg_side_effect(*args, **_kwargs):
        result = Mock()
        result.returncode = 0
        result.stdout = ""
        result.stderr = "Duration: 00:15:00"  # Each file is 15 minutes
        return result

    mock_run.side_effect = mock_ffmpeg_side_effect

    processor = AudiobookProcessor(options)
    output_file = processor.process()

    # Verify basic processing occurred
    calls = mock_run.call_args_list
    assert len(calls) > 0, "No ffmpeg calls were made"

    # Verify chapters file was created with correct structure
    chapters_file = output_dir / "chapters.txt"
    assert chapters_file.exists()
    chapter_content = chapters_file.read_text().splitlines()
    
    # Should have 4 chapters (from our sample files)
    assert len(chapter_content) == 4
    
    # Each line should be in format "HH:MM:SS Chapter Name"
    for line in chapter_content:
        assert re.match(r"\d{2}:\d{2}:\d{2} Chapter \d+.*", line)

    # Verify output is M4B
    assert output_file.suffix == ".m4b"
