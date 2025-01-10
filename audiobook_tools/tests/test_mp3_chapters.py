"""Tests for processing MP3 files with chapter information in filenames."""

# pylint: disable=redefined-outer-name
# This is expected for pytest fixtures

# pylint: disable=duplicate-code
# Duplicate code in test files is acceptable as it makes tests more readable
# and maintainable by keeping test data close to the tests that use it

import re
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner

from audiobook_tools.cli.main import cli
from audiobook_tools.core.processor import AudiobookProcessor, ProcessingOptions
from audiobook_tools.tests.test_utils import (
    create_mock_ffmpeg_duration,
    create_test_options,
    verify_chapters,
)
from audiobook_tools.utils.audio import AudioProcessingError


@pytest.fixture
def mp3_files_dir(tmp_path: Path) -> Path:
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
    mp3_files_dir: Path,
):
    """Test that we can detect MP3 files and extract chapter information."""
    # Should find all MP3s recursively
    mp3_files = sorted(mp3_files_dir.rglob("*.mp3"))
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
def test_process_mp3_files(mock_run: Mock, mp3_files_dir: Path, tmp_path: Path):
    """Test processing MP3 files into M4B with chapters."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    # Create test options
    metadata, audio_config = create_test_options()

    # Create processing options
    options = ProcessingOptions(
        input_dir=mp3_files_dir,
        output_dir=output_dir,
        output_format="m4b-ffmpeg",
        metadata=metadata,
        audio_config=audio_config,
        dry_run=False,
    )

    # Mock ffmpeg duration query
    durations = [
        ("CD1.*01", "00:30:00"),  # 30 min intro
        ("CD1.*02", "00:45:00"),  # 45 min chapter
        ("CD2", "00:20:00"),  # 20 min chapters
    ]
    mock_run.side_effect = create_mock_ffmpeg_duration(
        durations=durations,
        skip_patterns=["malformed"],
    ).side_effect

    processor = AudiobookProcessor(options)
    output_file = processor.process()

    # Verify chapters file was created with correct structure
    chapters_file = output_dir / "chapters.txt"
    assert chapters_file.exists()
    chapter_content = chapters_file.read_text().strip()

    # Verify exact format of chapters file
    expected_content = """;FFMETADATA1
[CHAPTER]
TIMEBASE=1/1
START=0
END=1800
title=Chapter 1 - Introduction
[CHAPTER]
TIMEBASE=1/1
START=1800
END=4500
title=Chapter 2 (1)
[CHAPTER]
TIMEBASE=1/1
START=4500
END=5700
title=Chapter 3 (1)
[CHAPTER]
TIMEBASE=1/1
START=5700
END=6900
title=Chapter 4 (1)
[CHAPTER]
TIMEBASE=1/1
START=6900
END=8100
title=Chapter 5 (1)""".strip()

    assert (
        chapter_content == expected_content
    ), "Chapters file should match expected format exactly"

    # Continue with existing tests using splitlines()
    chapter_lines = chapter_content.splitlines()

    # Should have header and 5 chapters (2 from CD1 + 3 from CD2, malformed file skipped)
    assert len(chapter_lines) > 5, "Should have header and chapters"
    assert chapter_lines[0] == ";FFMETADATA1", "Should have FFmpeg metadata header"

    # Verify chapter content
    # CD1 Chapter 1: 0 to 1800 (30 min)
    # CD1 Chapter 2: 1800 to 4500 (45 min)
    # CD2 Chapter 3: 4500 to 5700 (20 min)
    # CD2 Chapter 4: 5700 to 6900 (20 min)
    # CD2 Chapter 5: 6900 to 8100 (20 min)
    expected_chapters = [
        ("Chapter 1 - Introduction", 0, 1800),
        ("Chapter 2 (1)", 1800, 4500),
        ("Chapter 3 (1)", 4500, 5700),
        ("Chapter 4 (1)", 5700, 6900),
        ("Chapter 5 (1)", 6900, 8100),
    ]

    verify_chapters(chapter_lines, expected_chapters)

    # Verify output is M4B
    assert output_file.suffix == ".m4b"


@pytest.fixture
def flat_mp3_dir(tmp_path: Path) -> Path:
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
    flat_mp3_dir: Path,
):
    """Test that we can process MP3 files without CD directories."""
    # Should find all MP3s in the flat directory
    mp3_files = sorted(flat_mp3_dir.rglob("*.mp3"))
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
def test_process_flat_mp3_files(mock_run: Mock, flat_mp3_dir: Path, tmp_path: Path):
    """Test processing MP3 files without CD directories."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    # Create test options
    metadata, audio_config = create_test_options()

    # Create processing options
    options = ProcessingOptions(
        input_dir=flat_mp3_dir,
        output_dir=output_dir,
        output_format="m4b-ffmpeg",
        metadata=metadata,
        audio_config=audio_config,
        dry_run=False,
    )

    # Mock ffmpeg duration query - each chapter is 15 minutes
    durations = [(" - \\d+ -", "00:15:00")]  # Match any track number
    mock_run.side_effect = create_mock_ffmpeg_duration(durations=durations).side_effect

    processor = AudiobookProcessor(options)
    output_file = processor.process()

    # Verify chapters file was created with correct structure
    chapters_file = output_dir / "chapters.txt"
    assert chapters_file.exists()
    chapter_content = chapters_file.read_text().strip()

    # Verify exact format of chapters file
    expected_content = """;FFMETADATA1
[CHAPTER]
TIMEBASE=1/1
START=0
END=900
title=Chapter 1 - Introduction
[CHAPTER]
TIMEBASE=1/1
START=900
END=1800
title=Chapter 1 (1)
[CHAPTER]
TIMEBASE=1/1
START=1800
END=2700
title=Chapter 2 (1)
[CHAPTER]
TIMEBASE=1/1
START=2700
END=3600
title=Chapter 2 (2)
[CHAPTER]
TIMEBASE=1/1
START=3600
END=4500
title=Chapter 3 (1)
[CHAPTER]
TIMEBASE=1/1
START=4500
END=5400
title=Chapter 3 (2)
[CHAPTER]
TIMEBASE=1/1
START=5400
END=6300
title=Chapter 3 (3)
[CHAPTER]
TIMEBASE=1/1
START=6300
END=7200
title=Chapter 4 (1)
[CHAPTER]
TIMEBASE=1/1
START=7200
END=8100
title=Chapter 4 (2)
[CHAPTER]
TIMEBASE=1/1
START=8100
END=9000
title=Chapter 4 (3)
[CHAPTER]
TIMEBASE=1/1
START=9000
END=9900
title=Chapter 5 (1)
[CHAPTER]
TIMEBASE=1/1
START=9900
END=10800
title=Chapter 5 (2)
[CHAPTER]
TIMEBASE=1/1
START=10800
END=11700
title=Chapter 6 (1)
[CHAPTER]
TIMEBASE=1/1
START=11700
END=12600
title=Chapter 6 (2)
[CHAPTER]
TIMEBASE=1/1
START=12600
END=13500
title=Chapter 7 (1)
[CHAPTER]
TIMEBASE=1/1
START=13500
END=14400
title=Chapter 7 (2)""".strip()

    assert (
        chapter_content == expected_content
    ), "Chapters file should match expected format exactly"

    # Continue with existing tests using splitlines()
    chapter_lines = chapter_content.splitlines()

    # Should have header and all 16 chapters (no consolidation)
    assert len(chapter_lines) > 16, "Should have header and all chapters"
    assert chapter_lines[0] == ";FFMETADATA1", "Should have FFmpeg metadata header"

    # Each chapter should be 15 minutes (900 seconds)
    expected_chapters = [
        ("Chapter 1 - Introduction", 0, 900),
        ("Chapter 1 (1)", 900, 1800),
        ("Chapter 2 (1)", 1800, 2700),
        ("Chapter 2 (2)", 2700, 3600),
        ("Chapter 3 (1)", 3600, 4500),
        ("Chapter 3 (2)", 4500, 5400),
        ("Chapter 3 (3)", 5400, 6300),
        ("Chapter 4 (1)", 6300, 7200),
        ("Chapter 4 (2)", 7200, 8100),
        ("Chapter 4 (3)", 8100, 9000),
        ("Chapter 5 (1)", 9000, 9900),
        ("Chapter 5 (2)", 9900, 10800),
        ("Chapter 6 (1)", 10800, 11700),
        ("Chapter 6 (2)", 11700, 12600),
        ("Chapter 7 (1)", 12600, 13500),
        ("Chapter 7 (2)", 13500, 14400),
    ]

    verify_chapters(chapter_lines, expected_chapters)

    # Verify output is M4B
    assert output_file.suffix == ".m4b"


@pytest.fixture
def empty_dir(tmp_path: Path) -> Path:
    """Create an empty directory for testing error cases."""
    book_dir = tmp_path / "Empty Book"
    book_dir.mkdir()
    return book_dir


def test_no_valid_audio_files(empty_dir: Path, tmp_path: Path):
    """Test that we handle the case when no valid audio files are found."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    # Create test options
    metadata, audio_config = create_test_options()

    # Create processing options
    options = ProcessingOptions(
        input_dir=empty_dir,
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
def test_cli_command_no_audio_files(mock_run: Mock, empty_dir: Path, tmp_path: Path):
    """Test CLI command mode with explicit parameters when no audio files are found."""
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
            str(empty_dir),
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
    assert f"No valid FLAC or MP3 files found in {empty_dir}" in result.output
    assert "Error: " in result.output  # Click error prefix
    assert not mock_run.called  # No ffmpeg calls should be made
