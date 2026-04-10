"""Tests for audio operation modules."""

from pathlib import Path
from unittest.mock import patch, call

import pytest

from audiobook_tools.audio.merge import find_audio_files, _cd_sort_key


@pytest.fixture
def cd_structure(tmp_path):
    """Create a directory with CD-structured FLAC files."""
    for i in range(1, 4):
        cd_dir = tmp_path / f"CD{i}"
        cd_dir.mkdir()
        (cd_dir / f"CD{i}.flac").touch()
    return tmp_path


class TestFindAudioFiles:
    def test_finds_flac_files(self, cd_structure):
        files = find_audio_files(cd_structure, "flac")
        assert len(files) == 3

    def test_sorted_by_cd_number(self, cd_structure):
        files = find_audio_files(cd_structure, "flac")
        names = [f.name for f in files]
        assert names == ["CD1.flac", "CD2.flac", "CD3.flac"]

    def test_empty_directory(self, tmp_path):
        files = find_audio_files(tmp_path, "flac")
        assert files == []


class TestCdSortKey:
    def test_extracts_number(self):
        assert _cd_sort_key(Path("foo/CD1/bar.flac")) == 1
        assert _cd_sort_key(Path("foo/CD10/bar.flac")) == 10

    def test_no_cd_pattern(self):
        assert _cd_sort_key(Path("foo/bar.flac")) == 0
