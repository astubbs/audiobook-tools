"""Tests for CUE sheet combining functionality."""

from pathlib import Path
from unittest.mock import patch

from audiobook_tools.core.cue import CueProcessor


def test_time_to_seconds():
    """Test conversion of time string to seconds."""
    processor = CueProcessor(Path("."), Path("."))
    assert processor.time_to_seconds("00:00:00") == 0
    assert processor.time_to_seconds("00:01:00") == 1
    assert processor.time_to_seconds("01:00:00") == 60
    assert processor.time_to_seconds("00:00:74") == 74 / 75  # 74 frames at 75fps


def test_seconds_to_time():
    """Test conversion of seconds to time string."""
    processor = CueProcessor(Path("."), Path("."))
    assert processor.seconds_to_time(0) == "00:00:00"
    assert processor.seconds_to_time(1) == "00:01:00"
    assert processor.seconds_to_time(60) == "01:00:00"
    assert processor.seconds_to_time(74 / 75) == "00:00:74"


def test_parse_cue_file(tmp_path):
    """Test parsing a CUE file."""
    # Create test CUE files
    cue1 = tmp_path / "cd1.cue"
    cue2 = tmp_path / "cd2.cue"

    # Write test content
    cue1.write_text('FILE "cd1.flac" WAVE\n  TRACK 01 AUDIO\n    INDEX 01 00:00:00')
    cue2.write_text('FILE "cd2.flac" WAVE\n  TRACK 01 AUDIO\n    INDEX 01 00:00:00')

    # Create test FLAC files with durations
    flac1 = tmp_path / "cd1.flac"
    flac2 = tmp_path / "cd2.flac"
    flac1.touch()
    flac2.touch()

    # Parse CUE files
    processor = CueProcessor(tmp_path, tmp_path)
    cue_sheet = processor.parse_cue_file(cue1)

    # Verify parsed content
    assert cue_sheet.audio_file == "cd1.flac"
    assert len(cue_sheet.tracks) == 1
    assert cue_sheet.tracks[0].number == 1
    assert cue_sheet.tracks[0].index[1] == "00:00:00"


@patch.object(CueProcessor, 'get_audio_length')
def test_combine_cue_sheets(mock_get_audio_length, tmp_path):
    """Test combining multiple CUE sheets into one."""
    # Mock audio file duration
    mock_get_audio_length.return_value = 300.0  # 5 minutes

    # Create test CUE files with track information
    cue1 = tmp_path / "CD1" / "cd1.cue"
    cue2 = tmp_path / "CD2" / "cd2.cue"

    # Create directories
    cue1.parent.mkdir(parents=True)
    cue2.parent.mkdir(parents=True)

    # Write test content with track metadata
    cue1_content = (
        'FILE "cd1.flac" WAVE\n'
        "  TRACK 01 AUDIO\n"
        '    TITLE "Track 1"\n'
        '    PERFORMER "Artist 1"\n'
        "    INDEX 01 00:00:00"
    )
    cue2_content = (
        'FILE "cd2.flac" WAVE\n'
        "  TRACK 01 AUDIO\n"
        '    TITLE "Track 2"\n'
        '    PERFORMER "Artist 2"\n'
        "    INDEX 01 00:00:00"
    )

    cue1.write_text(cue1_content)
    cue2.write_text(cue2_content)

    # Create test FLAC files
    flac1 = tmp_path / "CD1" / "cd1.flac"
    flac2 = tmp_path / "CD2" / "cd2.flac"
    flac1.touch()
    flac2.touch()

    # Process CUE sheets
    processor = CueProcessor(tmp_path, tmp_path)
    output_file = processor.process_directory()

    # Read combined content
    combined_content = output_file.read_text()

    # Verify combined content
    assert 'FILE "cd1.flac" WAVE' in combined_content
    assert 'FILE "cd2.flac" WAVE' in combined_content
    assert 'TITLE "Track 1"' in combined_content
    assert 'TITLE "Track 2"' in combined_content
    assert 'PERFORMER "Artist 1"' in combined_content
    assert 'PERFORMER "Artist 2"' in combined_content
