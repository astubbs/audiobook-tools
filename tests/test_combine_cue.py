import unittest
import os
import shutil
import sys
from pathlib import Path
import re
from unittest.mock import patch

# Add parent directory to path so we can import our main script
sys.path.append(str(Path(__file__).parent.parent))
from combine_cue import time_to_seconds, seconds_to_time, calculate_cumulative_duration, OUTPUT_FILE

class TestCombineCue(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method"""
        self.test_dir = Path("./tests/test_data/Eckhart Tolle - A New Earth")
        self.test_cue_files = [
            self.test_dir / "CD1/test1.cue",
            self.test_dir / "CD2/test2.cue"
        ]
        self.test_audio_files = [
            self.test_dir / "CD1/test1.flac",
            self.test_dir / "CD2/test2.flac"
        ]
        
        # Create test directories and files
        for cue_file, audio_file in zip(self.test_cue_files, self.test_audio_files):
            cue_file.parent.mkdir(parents=True, exist_ok=True)
            # Create empty audio files
            audio_file.touch()
        
        # Create test content - note that 65:30:24 is just where the last track starts
        cd1_content = """PERFORMER "Eckhart Tolle"
FILE "test1.flac" WAVE
  TRACK 01 AUDIO
    TITLE "Test Track 1"
    INDEX 01 00:00:00
  TRACK 13 AUDIO
    TITLE "Last Track CD1"
    INDEX 01 65:30:24
"""
        cd2_content = """PERFORMER "Eckhart Tolle"
FILE "test2.flac" WAVE
  TRACK 14 AUDIO
    TITLE "First Track CD2"
    INDEX 01 00:00:00
"""
        self.test_cue_files[0].write_text(cd1_content)
        self.test_cue_files[1].write_text(cd2_content)

    def tearDown(self):
        """Clean up test fixtures after each test method"""
        if self.test_dir.parent.exists():
            shutil.rmtree(self.test_dir.parent)

    @patch('combine_cue.get_audio_length')
    def test_cd2_start_time(self, mock_get_audio_length):
        """Test that CD2 starts at the actual end time of CD1"""
        # Mock the audio length of CD1 to be 70:00:00 (4200 seconds)
        mock_get_audio_length.return_value = 4200.0
        
        # Calculate CD2's start time directly
        cd2_start = calculate_cumulative_duration(self.test_cue_files, 1)  # 1 is the index for CD2
        
        print(f"\nDebug info:")
        print(f"Mock audio length: {mock_get_audio_length.return_value} seconds")
        print(f"CD2 start time in seconds: {cd2_start}")
        print(f"CD2 start time formatted: {seconds_to_time(cd2_start)}")
        print(f"Expected CD2 start: 4200.0 seconds (70:00:00)")
        
        self.assertAlmostEqual(
            4200.0,  # 70:00:00 in seconds
            cd2_start,
            places=1,
            msg=f"CD2 should start at 70:00:00 (end of CD1), but got {seconds_to_time(cd2_start)}"
        )

    def test_time_conversion(self):
        """Test time conversion functions with various edge cases"""
        test_cases = [
            ("00:00:00", 0.0),  # Start of CD
            ("01:00:00", 60.0),  # Exactly one minute
            ("00:01:00", 1.0),   # Exactly one second
            ("00:00:74", 0.987), # Maximum frames (74)
            ("65:30:24", 3930.32), # Original failing case
        ]
        
        for test_time, expected_seconds in test_cases:
            with self.subTest(time=test_time):
                seconds = time_to_seconds(test_time)
                self.assertAlmostEqual(seconds, expected_seconds, places=3,
                    msg=f"Converting {test_time} to seconds failed")
                converted_back = seconds_to_time(seconds)
                self.assertEqual(test_time, converted_back,
                    f"Round trip conversion failed: {test_time} -> {seconds} -> {converted_back}")

if __name__ == '__main__':
    unittest.main() 