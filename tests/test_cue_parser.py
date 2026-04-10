"""Tests for CUE sheet parsing and combining."""

import shutil
from pathlib import Path
from unittest.mock import patch

import pytest

from audiobook_tools.cue.combiner import calculate_cumulative_duration, combine_cue_sheets
from audiobook_tools.cue.parser import CueSheet, find_cue_files, parse_cue_file
from audiobook_tools.utils.time import seconds_to_cue_time


@pytest.fixture
def test_data_dir(tmp_path):
    """Create a test audiobook directory structure with CUE and audio files."""
    base = tmp_path / "Test Audiobook"

    cd1 = base / "CD1"
    cd1.mkdir(parents=True)
    (cd1 / "test1.flac").touch()
    (cd1 / "test1.cue").write_text(
        'PERFORMER "Test Author"\n'
        'FILE "test1.flac" WAVE\n'
        "  TRACK 01 AUDIO\n"
        '    TITLE "Chapter One"\n'
        "    INDEX 01 00:00:00\n"
        "  TRACK 02 AUDIO\n"
        '    TITLE "Chapter Two"\n'
        "    INDEX 01 30:15:37\n"
        "  TRACK 13 AUDIO\n"
        '    TITLE "Last Track CD1"\n'
        "    INDEX 01 65:30:24\n",
        encoding="utf-8",
    )

    cd2 = base / "CD2"
    cd2.mkdir(parents=True)
    (cd2 / "test2.flac").touch()
    (cd2 / "test2.cue").write_text(
        'PERFORMER "Test Author"\n'
        'FILE "test2.flac" WAVE\n'
        "  TRACK 14 AUDIO\n"
        '    TITLE "First Track CD2"\n'
        "    INDEX 01 00:00:00\n"
        "  TRACK 15 AUDIO\n"
        '    TITLE "Second Track CD2"\n'
        "    INDEX 01 22:10:50\n",
        encoding="utf-8",
    )

    return base


class TestParseCueFile:
    def test_parses_tracks(self, test_data_dir):
        cue_path = test_data_dir / "CD1" / "test1.cue"
        sheet = parse_cue_file(cue_path)

        assert sheet.audio_filename == "test1.flac"
        assert sheet.performer == "Test Author"
        assert len(sheet.tracks) == 3
        assert sheet.tracks[0].title == "Chapter One"
        assert sheet.tracks[0].index_time == "00:00:00"
        assert sheet.tracks[2].title == "Last Track CD1"
        assert sheet.tracks[2].index_time == "65:30:24"

    def test_track_numbers_preserved(self, test_data_dir):
        sheet = parse_cue_file(test_data_dir / "CD1" / "test1.cue")
        assert sheet.tracks[0].number == 1
        assert sheet.tracks[2].number == 13


class TestFindCueFiles:
    def test_finds_and_sorts_by_cd_number(self, test_data_dir):
        cue_files = find_cue_files(test_data_dir)
        assert len(cue_files) == 2
        assert "CD1" in str(cue_files[0])
        assert "CD2" in str(cue_files[1])


class TestCumulativeDuration:
    def test_first_cd_starts_at_zero(self, test_data_dir):
        sheets = [parse_cue_file(f) for f in find_cue_files(test_data_dir)]
        assert calculate_cumulative_duration(sheets, 0) == 0.0

    @patch("audiobook_tools.cue.combiner.get_duration_seconds")
    def test_second_cd_starts_after_first(self, mock_duration, test_data_dir):
        mock_duration.return_value = 4200.0  # 70 minutes
        sheets = [parse_cue_file(f) for f in find_cue_files(test_data_dir)]

        cd2_start = calculate_cumulative_duration(sheets, 1)
        assert cd2_start == pytest.approx(4200.0)
        assert seconds_to_cue_time(cd2_start) == "70:00:00"


class TestCombineCueSheets:
    @patch("audiobook_tools.cue.combiner.get_duration_seconds")
    def test_combines_sheets(self, mock_duration, test_data_dir, tmp_path):
        mock_duration.return_value = 4200.0
        output = tmp_path / "out" / "combined.cue"

        combine_cue_sheets(test_data_dir, output)

        assert output.exists()
        content = output.read_text()
        # Track numbering should be sequential 1-5
        assert "TRACK 01 AUDIO" in content
        assert "TRACK 05 AUDIO" in content
        # CD2 tracks should have adjusted timestamps
        assert "Chapter One" in content
        assert "First Track CD2" in content
