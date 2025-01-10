"""Tests for processing MP3 files with chapter information in filenames."""

import re
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from audiobook_tools.common import AudiobookMetadata
from audiobook_tools.core.processor import AudiobookProcessor, ProcessingOptions
from audiobook_tools.utils.audio import AudioConfig, AudioProcessingError


@pytest.fixture
def sample_mp3_files(tmp_path: Path) -> Path:  # pylint: disable=redefined-outer-name
    """Create a sample directory with MP3 files that have chapter information in filenames."""
    book_dir = tmp_path / "Test Author - Test Book (Audio Book)"
    book_dir.mkdir()

    cd1_dir = book_dir / "CD1"
    cd2_dir = book_dir / "CD2"
    cd1_dir.mkdir()
    cd2_dir.mkdir()

    # Create sample MP3 files with different structures
    cd1_files = [
        "Test Author - Test Book (Audio Book) CD1 - 01 - Chapter 1 - Introduction.mp3",
        "Test Author - Test Book (Audio Book) CD1 - 02 - Chapter 2.mp3",
        "malformed.mp3",  # Should be skipped
    ]

    cd2_files = [
        "Test Author - Test Book (Audio Book) CD2 - 01 - Chapter 3.mp3",
        "Test Author - Test Book (Audio Book) CD2 - 02 - Chapter 4.mp3",
        "Test Author - Test Book (Audio Book) CD2 - 03 - Chapter 5.mp3",
    ]

    # Create the files with some content to make them look like MP3s
    mp3_header = bytes.fromhex("494433")  # ID3 tag

    for filename in cd1_files:
        with open(cd1_dir / filename, "wb") as f:
            f.write(mp3_header)

    for filename in cd2_files:
        with open(cd2_dir / filename, "wb") as f:
            f.write(mp3_header)

    return book_dir


def test_detect_mp3_chapters(
    sample_mp3_files: Path,
):  # pylint: disable=redefined-outer-name
    """Test that we can detect MP3 files and extract chapter information."""
    # Should find all MP3s recursively
    mp3_files = sorted(sample_mp3_files.rglob("*.mp3"))
    assert len(mp3_files) == 6  # Total across all CDs including malformed

    # Test filename pattern matching
    pattern = re.compile(r".*?CD(\d+).*? - (\d+) - (Chapter \d+.*?)\.mp3$")

    # Verify malformed files don't match pattern
    malformed_file = next(f for f in mp3_files if "malformed" in str(f))
    assert pattern.search(str(malformed_file)) is None

    # Check CD1 first file
    match = pattern.search(
        str(next(f for f in mp3_files if "CD1" in str(f) and "01" in str(f)))
    )
    assert match is not None
    assert match.group(1) == "1"  # CD number
    assert match.group(2) == "01"  # Track number
    assert match.group(3) == "Chapter 1 - Introduction"

    # Check CD2 first file
    match = pattern.search(
        str(next(f for f in mp3_files if "CD2" in str(f) and "01" in str(f)))
    )
    assert match is not None
    assert match.group(1) == "2"  # CD number
    assert match.group(2) == "01"  # Track number
    assert match.group(3) == "Chapter 3"  # Chapters continue from CD1


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

    # Mock ffmpeg duration query with different durations for each file
    def mock_ffmpeg_side_effect(*args, **_kwargs):
        result = Mock()
        result.returncode = 0
        result.stdout = ""

        # Extract CD and track info from the input file path
        input_file = str(args[0][2])  # ffmpeg -i <input_file>
        if "malformed" in input_file:
            # Malformed files should be skipped, not queried for duration
            raise AssertionError("Malformed file should not be processed")
        if "CD1" in input_file:
            if "01" in input_file:
                result.stderr = "Duration: 00:30:00"  # 30 min intro
            elif "02" in input_file:
                result.stderr = "Duration: 00:45:00"  # 45 min chapter
        elif "CD2" in input_file:
            result.stderr = "Duration: 00:20:00"  # 20 min chapters
        else:
            result.stderr = ""
        return result

    mock_run.side_effect = mock_ffmpeg_side_effect

    processor = AudiobookProcessor(options)
    output_file = processor.process()

    # Verify chapters file was created with correct structure
    chapters_file = output_dir / "chapters.txt"
    assert chapters_file.exists()
    chapter_content = chapters_file.read_text().splitlines()

    # Should have header and 5 chapters (2 from CD1 + 3 from CD2, malformed file skipped)
    assert len(chapter_content) > 5, "Should have header and chapters"
    assert chapter_content[0] == ";FFMETADATA1", "Should have FFmpeg metadata header"

    # Verify chapter content
    # CD1 Chapter 1: 0 to 1800 (30 min)
    # CD1 Chapter 2: 1800 to 4500 (45 min)
    # CD2 Chapter 3: 4500 to 5700 (20 min)
    # CD2 Chapter 4: 5700 to 6900 (20 min)
    # CD2 Chapter 5: 6900 to 8100 (20 min)
    expected_chapters = [
        ("Chapter 1 - Introduction", 0, 1800),
        ("Chapter 2", 1800, 4500),
        ("Chapter 3", 4500, 5700),
        ("Chapter 4", 5700, 6900),
        ("Chapter 5", 6900, 8100),
    ]

    chapter_idx = 0
    for i, line in enumerate(chapter_content):
        if line == "[CHAPTER]":
            title = None
            start = None
            end = None
            for j in range(i + 1, min(i + 5, len(chapter_content))):
                if chapter_content[j].startswith("TIMEBASE="):
                    assert chapter_content[j] == "TIMEBASE=1/1"
                elif chapter_content[j].startswith("START="):
                    start = int(chapter_content[j].split("=")[1])
                elif chapter_content[j].startswith("END="):
                    end = int(chapter_content[j].split("=")[1])
                elif chapter_content[j].startswith("title="):
                    title = chapter_content[j].split("=")[1]

            if title and start is not None and end is not None:
                expected_title, expected_start, expected_end = expected_chapters[chapter_idx]
                assert title == expected_title
                assert start == expected_start
                assert end == expected_end
                chapter_idx += 1

    assert chapter_idx == len(expected_chapters), "All chapters should be found"

    # Verify output is M4B
    assert output_file.suffix == ".m4b"


@pytest.fixture
def sample_flat_mp3_files(
    tmp_path: Path,
) -> Path:  # pylint: disable=redefined-outer-name
    """Create a sample directory with MP3 files in a flat structure (no CD subdirs)."""
    book_dir = tmp_path / "Test Author - Test Book (Audio Book)"
    book_dir.mkdir()

    # Create sample MP3 files with chapter numbers in filenames
    filenames = [
        "Test Author - Test Book (Audio Book) - 01 - Chapter 1 - Introduction.mp3",
        "Test Author - Test Book (Audio Book) - 02 - Chapter 1.mp3",
        "Test Author - Test Book (Audio Book) - 03 - Chapter 2.mp3",
        "Test Author - Test Book (Audio Book) - 04 - Chapter 2.mp3",
        "Test Author - Test Book (Audio Book) - 05 - Chapter 3.mp3",
        "Test Author - Test Book (Audio Book) - 06 - Chapter 3.mp3",
        "Test Author - Test Book (Audio Book) - 07 - Chapter 3.mp3",
        "Test Author - Test Book (Audio Book) - 08 - Chapter 4.mp3",
        "Test Author - Test Book (Audio Book) - 09 - Chapter 4.mp3",
        "Test Author - Test Book (Audio Book) - 10 - Chapter 4.mp3",
        "Test Author - Test Book (Audio Book) - 11 - Chapter 5.mp3",
        "Test Author - Test Book (Audio Book) - 12 - Chapter 5.mp3",
        "Test Author - Test Book (Audio Book) - 13 - Chapter 6.mp3",
        "Test Author - Test Book (Audio Book) - 14 - Chapter 6.mp3",
        "Test Author - Test Book (Audio Book) - 15 - Chapter 7.mp3",
        "Test Author - Test Book (Audio Book) - 16 - Chapter 7.mp3",
    ]

    # Create the files with some content to make them look like MP3s
    mp3_header = bytes.fromhex("494433")  # ID3 tag
    for filename in filenames:
        with open(book_dir / filename, "wb") as f:
            f.write(mp3_header)

    return book_dir


def test_flat_mp3_structure(
    sample_flat_mp3_files: Path,
):  # pylint: disable=redefined-outer-name
    """Test that we can process MP3 files without CD directories."""
    # Should find all MP3s in the flat directory
    mp3_files = sorted(sample_flat_mp3_files.rglob("*.mp3"))
    assert len(mp3_files) == 16  # Total number of chapters

    # Test filename pattern matching
    pattern = re.compile(r".*? - (\d+) - (Chapter \d+.*?)\.mp3$")

    # Check first file
    match = pattern.search(str(mp3_files[0]))
    assert match is not None
    assert match.group(1) == "01"  # Track number
    assert match.group(2) == "Chapter 1 - Introduction"

    # Check last file
    match = pattern.search(str(mp3_files[-1]))
    assert match is not None
    assert match.group(1) == "16"  # Track number
    assert match.group(2) == "Chapter 7"


@patch("audiobook_tools.utils.audio.subprocess.run")
def test_process_flat_mp3_files(
    mock_run: Mock, sample_flat_mp3_files: Path, tmp_path: Path
):  # pylint: disable=redefined-outer-name
    """Test processing MP3 files without CD directories."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    metadata = AudiobookMetadata(
        title="Test Book", artist="Test Author", cover_art=None
    )

    audio_config = AudioConfig(bitrate="64k")

    # Create processing options
    options = ProcessingOptions(
        input_dir=sample_flat_mp3_files,
        output_dir=output_dir,
        output_format="m4b-ffmpeg",
        metadata=metadata,
        audio_config=audio_config,
        dry_run=False,
    )

    # Mock ffmpeg duration query with different durations for each file
    def mock_ffmpeg_side_effect(*args, **_kwargs):
        result = Mock()
        result.returncode = 0
        result.stdout = ""

        # Extract track number from input file path
        input_file = str(args[0][2])  # ffmpeg -i <input_file>
        track_match = re.search(r" - (\d+) -", input_file)
        if not track_match:
            result.stderr = ""
            return result

        # Each chapter is 15 minutes
        result.stderr = "Duration: 00:15:00"
        return result

    mock_run.side_effect = mock_ffmpeg_side_effect

    processor = AudiobookProcessor(options)
    output_file = processor.process()

    # Verify chapters file was created with correct structure
    chapters_file = output_dir / "chapters.txt"
    assert chapters_file.exists()
    chapter_content = chapters_file.read_text().splitlines()

    # Should have header and 16 chapters
    assert len(chapter_content) > 16, "Should have header and chapters"
    assert chapter_content[0] == ";FFMETADATA1", "Should have FFmpeg metadata header"

    # Each chapter should be 15 minutes (900 seconds) after the previous one
    chapter_numbers = [1, 1, 2, 2, 3, 3, 3, 4, 4, 4, 5, 5, 6, 6, 7, 7]  # From filenames
    chapter_names = ["Chapter 1 - Introduction"] + [
        f"Chapter {num}" for num in chapter_numbers[1:]
    ]

    chapter_idx = 0
    for i, line in enumerate(chapter_content):
        if line == "[CHAPTER]":
            title = None
            start = None
            end = None
            for j in range(i + 1, min(i + 5, len(chapter_content))):
                if chapter_content[j].startswith("TIMEBASE="):
                    assert chapter_content[j] == "TIMEBASE=1/1"
                elif chapter_content[j].startswith("START="):
                    start = int(chapter_content[j].split("=")[1])
                elif chapter_content[j].startswith("END="):
                    end = int(chapter_content[j].split("=")[1])
                elif chapter_content[j].startswith("title="):
                    title = chapter_content[j].split("=")[1]

            if title and start is not None and end is not None:
                expected_title = chapter_names[chapter_idx]
                expected_start = chapter_idx * 900  # 15 minutes = 900 seconds
                expected_end = (chapter_idx + 1) * 900

                assert title == expected_title
                assert start == expected_start
                assert end == expected_end
                chapter_idx += 1

    assert chapter_idx == len(chapter_names), "All chapters should be found"

    # Verify output is M4B
    assert output_file.suffix == ".m4b"


@pytest.fixture
def empty_directory(tmp_path: Path) -> Path:  # pylint: disable=redefined-outer-name
    """Create an empty directory for testing error cases."""
    book_dir = tmp_path / "Empty Book"
    book_dir.mkdir()
    return book_dir


def test_no_valid_audio_files(empty_directory: Path, tmp_path: Path):
    """Test that we handle the case when no valid audio files are found."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    metadata = AudiobookMetadata(
        title="Test Book", artist="Test Author", cover_art=None
    )

    audio_config = AudioConfig(bitrate="64k")

    # Create processing options
    options = ProcessingOptions(
        input_dir=empty_directory,
        output_dir=output_dir,
        output_format="m4b-ffmpeg",
        metadata=metadata,
        audio_config=audio_config,
        dry_run=False,
    )

    processor = AudiobookProcessor(options)

    with pytest.raises(
        AudioProcessingError, match="No valid FLAC or MP3 files found in .*"
    ):
        processor.process()


@patch("audiobook_tools.utils.audio.subprocess.run")
def test_cli_command_no_audio_files(
    mock_run: Mock, empty_directory: Path, tmp_path: Path
):
    """Test CLI command mode with explicit parameters when no audio files are found."""
    from click.testing import CliRunner

    from audiobook_tools.cli.main import cli

    output_dir = tmp_path / "output"
    output_dir.mkdir()

    # Mock subprocess.run to avoid actual ffmpeg calls
    mock_run.return_value.returncode = 0
    mock_run.return_value.stdout = ""
    mock_run.return_value.stderr = ""

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "process",
            str(empty_directory),
            "--output-dir",
            str(output_dir),
            "--title",
            "Test Book",
            "--artist",
            "Test Author",
            "--no-interactive",
        ],
    )

    assert result.exit_code == 1
    assert f"No valid FLAC or MP3 files found in {empty_directory}" in result.output
    assert "Error: " in result.output  # Click error prefix
    assert not mock_run.called  # No ffmpeg calls should be made
