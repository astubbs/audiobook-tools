"""Tests for external tool checking utilities."""

from unittest.mock import patch

import pytest

from audiobook_tools.utils.external import check_tool, require_tool


def test_check_tool_found():
    with patch("shutil.which", return_value="/usr/bin/ffmpeg"):
        assert check_tool("ffmpeg") is True


def test_check_tool_missing():
    with patch("shutil.which", return_value=None):
        assert check_tool("nonexistent") is False


def test_require_tool_found():
    with patch("shutil.which", return_value="/usr/bin/ffmpeg"):
        require_tool("ffmpeg")  # should not raise


def test_require_tool_missing():
    with patch("shutil.which", return_value=None), pytest.raises(SystemExit):
        require_tool("nonexistent")
