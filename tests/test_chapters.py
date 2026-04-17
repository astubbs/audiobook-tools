"""Tests for chapter generation modules."""

from unittest.mock import patch

import pytest

from audiobook_tools.chapters.ffmpeg import generate_ffmetadata
from audiobook_tools.chapters.mp4box import generate_mp4box_chapters


@pytest.fixture
def sample_cue(tmp_path):
    """Create a sample combined CUE file."""
    cue = tmp_path / "combined.cue"
    cue.write_text(
        'FILE "combined.flac" WAVE\n'
        "  TRACK 01 AUDIO\n"
        '    TITLE "Introduction"\n'
        "    INDEX 01 00:00:00\n"
        "  TRACK 02 AUDIO\n"
        '    TITLE "Chapter One"\n'
        "    INDEX 01 05:30:25\n"
        "  TRACK 03 AUDIO\n"
        '    TITLE "Chapter Two"\n'
        "    INDEX 01 70:00:00\n",
        encoding="utf-8",
    )
    return cue


class TestFFmpegChapters:
    @patch("audiobook_tools.chapters.ffmpeg.get_duration_ms")
    def test_generates_metadata(self, mock_duration, sample_cue, tmp_path):
        mock_duration.return_value = 5400000  # 90 minutes
        audio = tmp_path / "combined.flac"
        audio.touch()
        output = tmp_path / "chapters.txt"

        count = generate_ffmetadata(sample_cue, audio, output)

        assert count == 3
        content = output.read_text()
        assert ";FFMETADATA1" in content
        assert "START=0" in content
        assert "title=Introduction" in content
        assert "title=Chapter One" in content
        assert "title=Chapter Two" in content
        # Last chapter should end at actual duration, not a hack
        assert "END=5400000" in content

    @patch("audiobook_tools.chapters.ffmpeg.get_duration_ms")
    def test_chapter_end_times_are_next_start(self, mock_duration, sample_cue, tmp_path):
        mock_duration.return_value = 5400000
        audio = tmp_path / "combined.flac"
        audio.touch()
        output = tmp_path / "chapters.txt"

        generate_ffmetadata(sample_cue, audio, output)

        content = output.read_text()
        # Chapter 1 (Introduction) should end where Chapter 2 (Chapter One) starts
        # 05:30:25 = 5*60*1000 + 30*1000 + 25*1000//75 = 330333
        assert "END=330333" in content


class TestMP4BoxChapters:
    def test_generates_chapters(self, sample_cue, tmp_path):
        output = tmp_path / "chapters.txt"

        count = generate_mp4box_chapters(sample_cue, output)

        assert count == 3
        content = output.read_text()
        assert "00:00:00.000 Introduction" in content
        assert "Chapter One" in content
        assert "Chapter Two" in content

    def test_empty_cue(self, tmp_path):
        empty_cue = tmp_path / "empty.cue"
        empty_cue.write_text("", encoding="utf-8")
        output = tmp_path / "chapters.txt"

        count = generate_mp4box_chapters(empty_cue, output)

        assert count == 0
        assert not output.exists()
