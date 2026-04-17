"""Tests for the CLI."""

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
