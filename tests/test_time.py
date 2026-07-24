"""Tests for time conversion utilities."""

import pytest

from audiobook_tools.utils.time import (
    cue_time_to_ms,
    cue_time_to_seconds,
    ms_to_timestamp,
    seconds_to_cue_time,
)


class TestCueTimeToSeconds:
    def test_zero(self):
        assert cue_time_to_seconds("00:00:00") == 0.0

    def test_one_minute(self):
        assert cue_time_to_seconds("01:00:00") == 60.0

    def test_one_second(self):
        assert cue_time_to_seconds("00:01:00") == 1.0

    def test_max_frames(self):
        assert cue_time_to_seconds("00:00:74") == pytest.approx(0.987, abs=0.001)

    def test_complex_time(self):
        assert cue_time_to_seconds("65:30:24") == pytest.approx(3930.32, abs=0.01)


class TestSecondsToAndFromCueTime:
    """Test round-trip conversion between seconds and CUE time."""

    @pytest.mark.parametrize(
        "cue_time,expected_seconds",
        [
            ("00:00:00", 0.0),
            ("01:00:00", 60.0),
            ("00:01:00", 1.0),
            ("00:00:74", 0.987),
            ("65:30:24", 3930.32),
        ],
    )
    def test_round_trip(self, cue_time, expected_seconds):
        seconds = cue_time_to_seconds(cue_time)
        assert seconds == pytest.approx(expected_seconds, abs=0.01)
        assert seconds_to_cue_time(seconds) == cue_time


class TestCueTimeToMs:
    def test_zero(self):
        assert cue_time_to_ms("00:00:00") == 0

    def test_one_minute(self):
        assert cue_time_to_ms("01:00:00") == 60000

    def test_one_second(self):
        assert cue_time_to_ms("00:01:00") == 1000

    def test_frames(self):
        # 37 frames = 37 * 1000 // 75 = 493 ms
        assert cue_time_to_ms("00:00:37") == 493

    def test_complex_time(self):
        # 65:30:24 = (65*60+30)*1000 + 24*1000//75 = 3930000 + 320 = 3930320
        assert cue_time_to_ms("65:30:24") == 3930320


class TestMsToTimestamp:
    def test_zero(self):
        assert ms_to_timestamp(0) == "00:00:00.000"

    def test_one_hour(self):
        assert ms_to_timestamp(3600000) == "01:00:00.000"

    def test_complex(self):
        # 1h 23m 45s 678ms = 5025678 ms
        assert ms_to_timestamp(5025678) == "01:23:45.678"

    def test_sub_second(self):
        assert ms_to_timestamp(123) == "00:00:00.123"
