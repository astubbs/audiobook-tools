"""Tests for the ffprobe duration wrapper."""

import json
from unittest.mock import MagicMock, patch

from audiobook_tools.audio.probe import get_duration_ms, get_duration_seconds


def _ffprobe_result(duration_str):
    result = MagicMock()
    result.stdout = json.dumps({"format": {"duration": duration_str}})
    return result


class TestProbe:
    def test_get_duration_seconds(self, tmp_path):
        with patch(
            "audiobook_tools.audio.probe.subprocess.run",
            return_value=_ffprobe_result("123.456"),
        ) as run:
            secs = get_duration_seconds(tmp_path / "a.flac")
        assert secs == 123.456
        # Uses ffprobe with JSON format output.
        cmd = run.call_args[0][0]
        assert cmd[0] == "ffprobe"
        assert "json" in cmd

    def test_get_duration_ms_rounds_to_int(self, tmp_path):
        with patch(
            "audiobook_tools.audio.probe.subprocess.run",
            return_value=_ffprobe_result("1.2345"),
        ):
            assert get_duration_ms(tmp_path / "a.flac") == 1234
