"""Tests for M4B creation command construction (FFmpeg and MP4Box)."""

from unittest.mock import patch

from audiobook_tools.audio.m4b import create_m4b_ffmpeg, create_m4b_mp4box


class TestCreateM4bFfmpeg:
    def test_basic_command(self, tmp_path):
        audio = tmp_path / "audiobook.aac"
        chapters = tmp_path / "chapters.txt"
        out = tmp_path / "audiobook.m4b"
        with (
            patch("audiobook_tools.audio.m4b.require_tool"),
            patch("audiobook_tools.audio.m4b.subprocess.run") as run,
        ):
            create_m4b_ffmpeg(audio, chapters, out)

        cmd = run.call_args[0][0]
        assert cmd[0] == "ffmpeg"
        # audio + chapters are both inputs; metadata mapped from the chapters input.
        assert cmd.count("-i") == 2
        assert "-map_metadata" in cmd and cmd[cmd.index("-map_metadata") + 1] == "1"
        assert "copy" in cmd
        assert str(out) in cmd

    def test_metadata_and_cover(self, tmp_path):
        audio = tmp_path / "audiobook.aac"
        chapters = tmp_path / "chapters.txt"
        cover = tmp_path / "cover.jpg"
        cover.touch()
        out = tmp_path / "audiobook.m4b"
        with (
            patch("audiobook_tools.audio.m4b.require_tool"),
            patch("audiobook_tools.audio.m4b.subprocess.run") as run,
        ):
            create_m4b_ffmpeg(
                audio, chapters, out, title="My Book", artist="An Author", cover_path=cover
            )

        cmd = run.call_args[0][0]
        assert cmd.count("-i") == 3  # audio + chapters + cover
        assert "attached_pic" in cmd
        assert "title=My Book" in cmd
        assert "artist=An Author" in cmd


class TestCreateM4bMp4box:
    def test_command(self, tmp_path):
        audio = tmp_path / "audiobook.aac"
        chapters = tmp_path / "chapters.txt"
        out = tmp_path / "audiobook.m4b"
        with (
            patch("audiobook_tools.audio.m4b.require_tool") as require,
            patch("audiobook_tools.audio.m4b.subprocess.run") as run,
        ):
            create_m4b_mp4box(audio, chapters, out)

        require.assert_called_once_with("MP4Box")
        cmd = run.call_args[0][0]
        assert cmd[0] == "MP4Box"
        assert "-add" in cmd and str(audio) in cmd
        assert "-chap" in cmd and str(chapters) in cmd
        assert str(out) in cmd
