"""Tests for the CLI."""

from unittest.mock import patch

from click.testing import CliRunner

from audiobook_tools.cli import main


class TestCLI:
    def test_version(self):
        runner = CliRunner()
        result = runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        assert "0.1.0" in result.output

    def test_help(self):
        runner = CliRunner()
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "convert" in result.output
        assert "combine-cue" in result.output
        assert "merge" in result.output
        assert "chapters" in result.output
        assert "check-tools" in result.output

    def test_convert_help(self):
        runner = CliRunner()
        result = runner.invoke(main, ["convert", "--help"])
        assert result.exit_code == 0
        assert "--bitrate" in result.output
        assert "--method" in result.output
        assert "--dry-run" in result.output
        assert "--resume" in result.output
        assert "--title" in result.output
        assert "--artist" in result.output
        assert "--cover" in result.output

    def test_convert_missing_dir(self):
        runner = CliRunner()
        result = runner.invoke(main, ["convert", "/nonexistent"])
        assert result.exit_code != 0

    def test_chapters_requires_audio_for_ffmpeg(self, tmp_path):
        cue = tmp_path / "test.cue"
        cue.write_text('  TRACK 01 AUDIO\n    TITLE "Test"\n    INDEX 01 00:00:00\n')
        runner = CliRunner()
        result = runner.invoke(main, ["chapters", str(cue)])
        assert result.exit_code != 0
        assert "--audio-file" in result.output

    def test_no_tui_shows_help(self):
        runner = CliRunner()
        result = runner.invoke(main, ["--no-tui"])
        assert result.exit_code == 0
        assert "convert" in result.output

    def test_tui_cancelled_returns_cleanly(self):
        runner = CliRunner()
        with patch("audiobook_tools.tui.display_welcome", return_value=None):
            result = runner.invoke(main, [])
        assert result.exit_code == 0
        assert "Cancelled" in result.output


class TestConvertEndToEnd:
    def test_mp3_pipeline(self, tmp_path):
        (tmp_path / "01 - Intro.mp3").touch()
        (tmp_path / "02 - Chapter One.mp3").touch()
        out_dir = tmp_path / "out"
        runner = CliRunner()
        with (
            patch("audiobook_tools.audio.merge.merge_mp3") as merge,
            patch("audiobook_tools.chapters.mp3.get_duration_ms", return_value=1000),
            patch("audiobook_tools.audio.encode.encode_to_aac") as encode,
            patch("audiobook_tools.audio.m4b.create_m4b_ffmpeg") as m4b,
            patch("audiobook_tools.audio.probe.get_duration_seconds", return_value=3600.0),
        ):
            result = runner.invoke(main, ["convert", str(tmp_path), "-o", str(out_dir)])

        assert result.exit_code == 0, result.output
        merge.assert_called_once()
        encode.assert_called_once()
        m4b.assert_called_once()
        chapters = (out_dir / "chapters.txt").read_text(encoding="utf-8")
        assert "title=Intro" in chapters
        assert "title=Chapter One" in chapters
        assert "Audiobook created" in result.output

    def test_dry_run_stops_after_merge(self, tmp_path):
        (tmp_path / "01 - Intro.mp3").touch()
        out_dir = tmp_path / "out"
        runner = CliRunner()
        with (
            patch("audiobook_tools.audio.merge.merge_mp3") as merge,
            patch("audiobook_tools.audio.encode.encode_to_aac") as encode,
            patch("audiobook_tools.audio.m4b.create_m4b_ffmpeg") as m4b,
        ):
            result = runner.invoke(
                main, ["convert", str(tmp_path), "-o", str(out_dir), "--dry-run"]
            )

        assert result.exit_code == 0, result.output
        merge.assert_called_once()
        encode.assert_not_called()
        m4b.assert_not_called()
        assert "Dry run complete" in result.output
