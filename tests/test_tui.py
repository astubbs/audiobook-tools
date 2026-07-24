"""Tests for the interactive TUI option-collection logic (prompts mocked)."""

from unittest.mock import patch

from audiobook_tools.tui import display_welcome


def _patches(browse_side_effect, method="1", confirm=True, metadata=None):
    """Common patch set for driving display_welcome without a real terminal."""
    metadata = metadata if metadata is not None else {"title": "T", "artist": "A"}
    return (
        patch("audiobook_tools.tui.browse_directory", side_effect=browse_side_effect),
        patch("audiobook_tools.tui.Prompt.ask", return_value=method),
        patch("audiobook_tools.tui.prompt_metadata", return_value=metadata),
        patch("audiobook_tools.tui.Confirm.ask", return_value=confirm),
    )


class TestDisplayWelcome:
    def test_happy_path_returns_convert_options(self, tmp_path):
        (tmp_path / "01 - Intro.mp3").touch()
        out = tmp_path / "out"
        p1, p2, p3, p4 = _patches([tmp_path, out], method="1")
        with p1, p2, p3, p4:
            opts = display_welcome()

        assert opts is not None
        assert opts["input_dir"] == tmp_path
        assert opts["output_dir"] == out
        assert opts["method"] == "ffmpeg"
        assert opts["bitrate"] == "64k"
        assert opts["dry_run"] is False
        assert opts["resume"] is False
        assert opts["title"] == "T"
        # Every returned key must be a valid `convert` parameter.
        valid = {
            "input_dir",
            "output_dir",
            "bitrate",
            "method",
            "title",
            "artist",
            "cover",
            "dry_run",
            "resume",
        }
        assert set(opts) <= valid

    def test_mp4box_choice(self, tmp_path):
        (tmp_path / "01 - Intro.mp3").touch()
        p1, p2, p3, p4 = _patches([tmp_path, tmp_path / "out"], method="2")
        with p1, p2, p3, p4:
            opts = display_welcome()
        assert opts["method"] == "mp4box"

    def test_cancel_at_input_returns_none(self):
        p1, p2, p3, p4 = _patches([None])
        with p1, p2, p3, p4:
            assert display_welcome() is None

    def test_decline_confirmation_returns_none(self, tmp_path):
        (tmp_path / "01 - Intro.mp3").touch()
        p1, p2, p3, p4 = _patches([tmp_path, tmp_path / "out"], confirm=False)
        with p1, p2, p3, p4:
            assert display_welcome() is None
