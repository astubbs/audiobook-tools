"""Tests for AAC encoding command construction."""

from unittest.mock import patch

from audiobook_tools.audio.encode import encode_to_aac


class TestEncodeToAac:
    def test_builds_expected_ffmpeg_command(self, tmp_path):
        inp = tmp_path / "in.flac"
        out = tmp_path / "sub" / "out.aac"
        with (
            patch("audiobook_tools.audio.encode.require_tool"),
            patch("audiobook_tools.audio.encode.subprocess.run") as run,
        ):
            encode_to_aac(inp, out, bitrate="96k")

        cmd = run.call_args[0][0]
        assert cmd[0] == "ffmpeg"
        assert "-c:a" in cmd and cmd[cmd.index("-c:a") + 1] == "aac"
        assert "-b:a" in cmd and cmd[cmd.index("-b:a") + 1] == "96k"
        assert "+faststart" in cmd
        assert str(inp) in cmd and str(out) in cmd
        # Output directory is created.
        assert out.parent.is_dir()

    def test_default_bitrate(self, tmp_path):
        with (
            patch("audiobook_tools.audio.encode.require_tool"),
            patch("audiobook_tools.audio.encode.subprocess.run") as run,
        ):
            encode_to_aac(tmp_path / "in.flac", tmp_path / "out.aac")
        cmd = run.call_args[0][0]
        assert cmd[cmd.index("-b:a") + 1] == "64k"

    def test_requires_ffmpeg(self, tmp_path):
        with (
            patch("audiobook_tools.audio.encode.require_tool") as require,
            patch("audiobook_tools.audio.encode.subprocess.run"),
        ):
            encode_to_aac(tmp_path / "in.flac", tmp_path / "out.aac")
        require.assert_called_once_with("ffmpeg")
