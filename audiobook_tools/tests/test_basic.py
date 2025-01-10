"""Basic test module for audiobook tools."""

import json
import os
from pathlib import Path
from unittest.mock import patch, Mock

import click
import pytest
from click.testing import CliRunner

from audiobook_tools.cli.main import cli


def test_basic():
    """Basic test to verify test discovery."""
    assert True


def test_cli_help():
    """Test that the CLI runs and shows help without errors."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "Audiobook Tools" in result.output


def test_cli_version():
    """Test that the CLI runs with --version flag."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0


@patch("audiobook_tools.cli.tui.display_welcome")
def test_cli_no_args(mock_display_welcome):
    """Test that the CLI runs without arguments and shows welcome screen."""
    mock_display_welcome.return_value = None  # Simulate user cancellation
    runner = CliRunner()
    result = runner.invoke(cli)
    assert result.exit_code == 0
    mock_display_welcome.assert_called_once()


@pytest.fixture
def mock_subprocess():
    """Mock subprocess.run for external commands."""
    patches = [
        patch("audiobook_tools.utils.audio.subprocess.run"),
        patch("audiobook_tools.core.cue.subprocess.run")
    ]

    def side_effect(cmd, *args, **kwargs):
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stderr = ""

        if cmd[0] == "sox":
            mock_result.stdout = ""
        elif cmd[0] == "ffmpeg":
            mock_result.stdout = ""
        elif cmd[0] == "ffprobe":
            mock_result.stdout = json.dumps({
                "format": {
                    "duration": "300.0"  # 5 minutes
                }
            })
        else:
            mock_result.stdout = ""

        return mock_result

    with patches[0] as mock_run_audio, patches[1] as mock_run_cue:
        mock_run_audio.side_effect = side_effect
        mock_run_cue.side_effect = side_effect
        mock_run_audio.reset_mock()
        mock_run_cue.reset_mock()
        yield mock_run_audio, mock_run_cue


@pytest.fixture
def sample_audiobook(tmp_path):
    """Create a sample audiobook directory structure."""
    book_dir = tmp_path / "Test Book"
    book_dir.mkdir()
    
    # Create CD1 directory with files
    cd1_dir = book_dir / "CD1"
    cd1_dir.mkdir()
    (cd1_dir / "CD1.flac").touch()
    (cd1_dir / "audiofile.cue").write_text(
        'FILE "CD1.flac" WAVE\n'
        "  TRACK 01 AUDIO\n"
        '    TITLE "Chapter 1"\n'
        "    INDEX 01 00:00:00"
    )
    
    # Create CD2 directory with files
    cd2_dir = book_dir / "CD2"
    cd2_dir.mkdir()
    (cd2_dir / "CD2.flac").touch()
    (cd2_dir / "audiofile.cue").write_text(
        'FILE "CD2.flac" WAVE\n'
        "  TRACK 01 AUDIO\n"
        '    TITLE "Chapter 2"\n'
        "    INDEX 01 00:00:00"
    )
    
    return book_dir


def test_process_command_with_mocked_services(mock_subprocess, sample_audiobook, tmp_path):
    """Test processing an audiobook with mocked external services."""
    mock_run_audio, mock_run_cue = mock_subprocess
    output_dir = tmp_path / "output"
    output_dir.mkdir(parents=True)
    
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "--no-tui",  # Disable TUI for testing
            "--debug",  # Enable debug logging
            "process",
            str(sample_audiobook),
            "--output-dir", str(output_dir),
            "--output-format", "m4b-ffmpeg",
            "--title", "Test Book",
            "--artist", "Test Author",
            "--no-interactive",  # Disable interactive prompts
        ]
    )
    
    # Print error output if the command failed
    if result.exit_code != 0:
        print(f"\nCommand failed with exit code {result.exit_code}")
        print("Output:", result.output)
        if result.exception:
            print("Exception:", result.exception)
            print("Traceback:", result.exc_info)
    
    assert result.exit_code == 0, f"Command failed with output:\n{result.output}"
    
    # Verify external commands were called
    audio_calls = mock_run_audio.call_args_list
    cue_calls = mock_run_cue.call_args_list
    
    # Get all commands called
    audio_commands = [call.args[0][0] for call in audio_calls]
    cue_commands = [call.args[0][0] for call in cue_calls]
    all_commands = audio_commands + cue_commands
    
    # Check that the expected commands were called
    assert "sox" in all_commands  # For merging FLAC files
    assert "ffmpeg" in all_commands  # For converting to AAC/M4B
    
    # Verify the order of operations
    assert len(audio_calls) + len(cue_calls) >= 3  # At least: sox merge, ffmpeg convert, ffmpeg create m4b


def test_combine_cue_command(mock_subprocess, sample_audiobook, tmp_path):
    """Test combining CUE sheets with mocked services."""
    mock_run_audio, mock_run_cue = mock_subprocess
    output_dir = tmp_path / "output"
    output_dir.mkdir(parents=True)
    
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "--no-tui",  # Disable TUI for testing
            "--debug",  # Enable debug logging
            "combine-cue",
            str(sample_audiobook),
            str(output_dir),
        ]
    )
    
    # Print error output if the command failed
    if result.exit_code != 0:
        print(f"\nCommand failed with exit code {result.exit_code}")
        print("Output:", result.output)
        if result.exception:
            print("Exception:", result.exception)
            print("Traceback:", result.exc_info)
    
    assert result.exit_code == 0, f"Command failed with output:\n{result.output}"
    
    # Verify the combined CUE file was created
    combined_cue = output_dir / "combined.cue"
    assert combined_cue.exists()
    
    # Check the content of the combined CUE file
    content = combined_cue.read_text()
    assert 'FILE "CD1.flac" WAVE' in content
    assert 'TITLE "Chapter 1"' in content
    assert 'TITLE "Chapter 2"' in content
