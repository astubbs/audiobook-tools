"""Test utilities and common fixtures for audiobook tools tests."""

import re
from typing import List, Optional, Tuple
from unittest.mock import Mock

from audiobook_tools.common import AudiobookMetadata
from audiobook_tools.utils.audio import AudioConfig


def create_test_options(
    title: str = "Test Book",
    artist: str = "Test Author",
    bitrate: str = "64k",
) -> Tuple[AudiobookMetadata, AudioConfig]:
    """Create common test metadata and audio config.

    Args:
        title: Title of the audiobook
        artist: Artist/author of the audiobook
        bitrate: Audio bitrate for encoding

    Returns:
        Tuple of (AudiobookMetadata, AudioConfig)
    """
    metadata = AudiobookMetadata(title=title, artist=artist, cover_art=None)
    audio_config = AudioConfig(bitrate=bitrate)
    return metadata, audio_config


def create_mock_ffmpeg_duration(
    durations: List[Tuple[str, str]],
    skip_patterns: Optional[List[str]] = None,
) -> Mock:
    """Create a mock ffmpeg duration query function.

    Args:
        durations: List of (pattern, duration) tuples for matching files
        skip_patterns: List of patterns that should raise AssertionError if matched
    """

    def mock_ffmpeg_side_effect(*args, **_kwargs):
        result = Mock()
        result.returncode = 0
        result.stdout = ""

        input_file = str(args[0][2])  # ffmpeg -i <input_file>

        # Check skip patterns first
        if skip_patterns:
            for pattern in skip_patterns:
                if pattern in input_file:
                    raise AssertionError(
                        f"File matching {pattern} should not be processed"
                    )

        # Match durations
        for pattern, duration in durations:
            if re.search(pattern, input_file):
                result.stderr = f"Duration: {duration}.00"
                return result

        result.stderr = ""
        return result

    return Mock(side_effect=mock_ffmpeg_side_effect)


def verify_chapters(
    chapter_content: List[str], expected_chapters: List[Tuple[str, int, int]]
):
    """Verify chapter content matches expected chapters.

    Args:
        chapter_content: List of lines from the chapters file
        expected_chapters: List of tuples (title, start, end) for expected chapters
    """
    chapter_idx = 0
    for i, line in enumerate(chapter_content):
        if line == "[CHAPTER]":
            title, start, end = None, None, None
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
                expected_title, expected_start, expected_end = expected_chapters[
                    chapter_idx
                ]
                assert title == expected_title
                assert start == expected_start
                assert end == expected_end
                chapter_idx += 1

    assert chapter_idx == len(expected_chapters), "All chapters should be found"
