"""Tests for audio merging command construction (sox / ffmpeg concat)."""

from unittest.mock import patch

import pytest

from audiobook_tools.audio.merge import merge_flac, merge_mp3


@pytest.fixture
def cd_flac(tmp_path):
    for i in (1, 2):
        d = tmp_path / f"CD{i}"
        d.mkdir()
        (d / f"CD{i}.flac").touch()
    return tmp_path


@pytest.fixture
def cd_mp3(tmp_path):
    for i in (1, 2):
        d = tmp_path / f"CD{i}"
        d.mkdir()
        (d / f"CD{i} - 01 - track.mp3").touch()
    return tmp_path


class TestMergeFlac:
    def test_dry_run_lists_without_calling_sox(self, cd_flac, tmp_path):
        out = tmp_path / "out" / "combined.flac"
        with (
            patch("audiobook_tools.audio.merge.require_tool"),
            patch("audiobook_tools.audio.merge.get_duration_seconds", return_value=60.0),
            patch("audiobook_tools.audio.merge.subprocess.run") as run,
        ):
            files = merge_flac(cd_flac, out, dry_run=True)
        assert len(files) == 2
        run.assert_not_called()

    def test_builds_sox_command(self, cd_flac, tmp_path):
        out = tmp_path / "out" / "combined.flac"
        with (
            patch("audiobook_tools.audio.merge.require_tool"),
            patch("audiobook_tools.audio.merge.get_duration_seconds", return_value=60.0),
            patch("audiobook_tools.audio.merge.subprocess.run") as run,
        ):
            merge_flac(cd_flac, out)
        cmd = run.call_args[0][0]
        assert cmd[0] == "sox"
        assert str(out) == cmd[-1]  # output is the last argument

    def test_no_files_raises(self, tmp_path):
        with (
            patch("audiobook_tools.audio.merge.require_tool"),
            patch("audiobook_tools.audio.merge.subprocess.run"),
            pytest.raises(FileNotFoundError),
        ):
            merge_flac(tmp_path, tmp_path / "out.flac")


class TestMergeMp3:
    def test_dry_run(self, cd_mp3, tmp_path):
        out = tmp_path / "out" / "combined.mp3"
        with (
            patch("audiobook_tools.audio.merge.require_tool"),
            patch("audiobook_tools.audio.merge.subprocess.run") as run,
        ):
            files = merge_mp3(cd_mp3, out, dry_run=True)
        assert len(files) == 2
        run.assert_not_called()

    def test_builds_ffmpeg_concat_and_cleans_up_list(self, cd_mp3, tmp_path):
        out = tmp_path / "out" / "combined.mp3"
        with (
            patch("audiobook_tools.audio.merge.require_tool"),
            patch("audiobook_tools.audio.merge.subprocess.run") as run,
        ):
            merge_mp3(cd_mp3, out)
        cmd = run.call_args[0][0]
        assert cmd[0] == "ffmpeg"
        assert "concat" in cmd
        assert "copy" in cmd
        # The temporary concat list is removed after use.
        assert not (out.parent / "concat_list.txt").exists()
