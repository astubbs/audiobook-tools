"""Tests for MP3 filename-based chapter generation and file ordering."""

from pathlib import Path
from unittest.mock import patch

from audiobook_tools.audio.merge import ordered_mp3_files
from audiobook_tools.chapters.mp3 import generate_mp3_chapters, title_from_filename


class TestTitleFromFilename:
    def test_strips_leading_track_number(self):
        assert title_from_filename(Path("01 - Introduction.mp3")) == "Introduction"

    def test_strips_cd_and_track_prefix(self):
        assert title_from_filename(Path("CD1 - 03 - The River.mp3")) == "The River"

    def test_plain_title_untouched(self):
        assert title_from_filename(Path("Prologue.mp3")) == "Prologue"

    def test_underscore_and_dot_separators(self):
        assert title_from_filename(Path("02_Chapter Two.mp3")) == "Chapter Two"

    def test_falls_back_to_stem_when_all_stripped(self):
        # A bare number stem would strip to empty; fall back to the stem.
        assert title_from_filename(Path("07.mp3")) == "07"


def _durations(mapping):
    """Return a get_duration_ms side_effect that looks up by filename stem."""

    def _lookup(path):
        return mapping[Path(path).name]

    return _lookup


class TestGenerateMp3Chapters:
    def test_cumulative_timestamps_and_exact_output(self, tmp_path):
        files = [Path("01 - Intro.mp3"), Path("02 - Chapter.mp3")]
        out = tmp_path / "chapters.txt"
        with patch(
            "audiobook_tools.chapters.mp3.get_duration_ms",
            side_effect=_durations({"01 - Intro.mp3": 1000, "02 - Chapter.mp3": 2000}),
        ):
            count = generate_mp3_chapters(files, out)

        assert count == 2
        assert out.read_text(encoding="utf-8") == (
            ";FFMETADATA1\n\n"
            "[CHAPTER]\nTIMEBASE=1/1000\nSTART=0\nEND=1000\ntitle=Intro\n\n"
            "[CHAPTER]\nTIMEBASE=1/1000\nSTART=1000\nEND=3000\ntitle=Chapter\n\n"
        )

    def test_duplicate_titles_are_disambiguated(self, tmp_path):
        # First occurrence stays clean; later ones get (2), (3).
        files = [
            Path("CD1 - 01 - Chapter.mp3"),
            Path("CD2 - 01 - Chapter.mp3"),
            Path("CD3 - 01 - Chapter.mp3"),
        ]
        out = tmp_path / "chapters.txt"
        with patch("audiobook_tools.chapters.mp3.get_duration_ms", return_value=1000):
            generate_mp3_chapters(files, out)

        text = out.read_text(encoding="utf-8")
        assert "title=Chapter\n" in text
        assert "title=Chapter (2)\n" in text
        assert "title=Chapter (3)\n" in text

    def test_skips_zero_duration_files(self, tmp_path):
        files = [Path("01 - Good.mp3"), Path("02 - Bad.mp3"), Path("03 - Good2.mp3")]
        out = tmp_path / "chapters.txt"
        with patch(
            "audiobook_tools.chapters.mp3.get_duration_ms",
            side_effect=_durations(
                {"01 - Good.mp3": 1000, "02 - Bad.mp3": 0, "03 - Good2.mp3": 1000}
            ),
        ):
            count = generate_mp3_chapters(files, out)

        assert count == 2
        text = out.read_text(encoding="utf-8")
        assert "title=Bad" not in text
        # Second good chapter starts right after the first (bad one contributed nothing).
        assert "START=1000" in text

    def test_empty_input_writes_nothing(self, tmp_path):
        out = tmp_path / "chapters.txt"
        assert generate_mp3_chapters([], out) == 0
        assert not out.exists()

    def test_mp4box_method_writes_mp4box_format(self, tmp_path):
        files = [Path("01 - Intro.mp3"), Path("02 - Chapter.mp3")]
        out = tmp_path / "chapters.txt"
        with patch(
            "audiobook_tools.chapters.mp3.get_duration_ms",
            side_effect=_durations({"01 - Intro.mp3": 1000, "02 - Chapter.mp3": 2000}),
        ):
            count = generate_mp3_chapters(files, out, method="mp4box")

        assert count == 2
        # MP4Box format is "HH:MM:SS.mmm Title", start times only, no FFMETADATA header.
        assert out.read_text(encoding="utf-8") == ("00:00:00.000 Intro\n00:00:01.000 Chapter\n")


class TestOrderedMp3Files:
    def test_cd_structured_order(self, tmp_path):
        (tmp_path / "CD2").mkdir()
        (tmp_path / "CD1").mkdir()
        f_cd1 = tmp_path / "CD1" / "01 - a.mp3"
        f_cd2 = tmp_path / "CD2" / "01 - b.mp3"
        f_cd2.touch()
        f_cd1.touch()

        ordered = ordered_mp3_files(tmp_path)
        assert ordered == [f_cd1, f_cd2]

    def test_flat_order_by_name(self, tmp_path):
        f2 = tmp_path / "02 - b.mp3"
        f1 = tmp_path / "01 - a.mp3"
        f2.touch()
        f1.touch()

        ordered = ordered_mp3_files(tmp_path)
        assert ordered == [f1, f2]

    def test_empty_dir(self, tmp_path):
        assert ordered_mp3_files(tmp_path) == []
