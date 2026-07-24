"""End-to-end integration tests that run the REAL conversion pipeline.

These exercise the actual external tools (ffmpeg / ffprobe / MP4Box) against small,
non-copyrighted spoken-word sample files under ``tests/data/sample_mp3`` (generated
with macOS ``say`` from original text). They are skipped automatically when the
required tools are not installed, so the mocked unit tests remain the portable default.
"""

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest
from click.testing import CliRunner

from audiobook_tools.cli import main

SAMPLE_MP3_DIR = Path(__file__).parent / "data" / "sample_mp3"
EXPECTED_TITLES = ["Introduction", "Chapter One", "Chapter Two"]

_have_ffmpeg = bool(shutil.which("ffmpeg") and shutil.which("ffprobe"))
requires_ffmpeg = pytest.mark.skipif(not _have_ffmpeg, reason="ffmpeg/ffprobe not installed")
requires_mp4box = pytest.mark.skipif(not shutil.which("MP4Box"), reason="MP4Box not installed")


def _probe(m4b: Path) -> dict:
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "quiet",
            "-print_format",
            "json",
            "-show_chapters",
            "-show_entries",
            "format=duration:format_tags=title,artist",
            str(m4b),
        ],
        capture_output=True,
        text=True,
        check=True,
        stdin=subprocess.DEVNULL,
    )
    return json.loads(result.stdout)


@requires_ffmpeg
class TestConvertMp3RealPipeline:
    def test_produces_chaptered_m4b(self, tmp_path):
        out_dir = tmp_path / "out"
        result = CliRunner().invoke(
            main,
            [
                "convert",
                str(SAMPLE_MP3_DIR),
                "-o",
                str(out_dir),
                "--title",
                "Sample Book",
                "--artist",
                "Test Author",
            ],
        )
        assert result.exit_code == 0, result.output
        m4b = out_dir / "audiobook.m4b"
        assert m4b.exists()

        data = _probe(m4b)
        titles = [c["tags"]["title"] for c in data["chapters"]]
        assert titles == EXPECTED_TITLES
        # Chapters are contiguous and cover the whole book.
        assert float(data["chapters"][0]["start_time"]) == 0.0
        # Duration is roughly the sum of the inputs (~15s); allow encoder tolerance.
        assert 13.0 < float(data["format"]["duration"]) < 18.0
        # Metadata is embedded.
        assert data["format"]["tags"]["title"] == "Sample Book"
        assert data["format"]["tags"]["artist"] == "Test Author"

    def test_relative_input_from_other_cwd(self, tmp_path, monkeypatch):
        """Regression: a relative input dir with a separate output dir must work.

        The ffmpeg concat list must contain absolute paths, since the concat demuxer
        resolves relative entries against the list file's directory, not the CWD.
        """
        monkeypatch.chdir(tmp_path)
        rel_input = os.path.relpath(SAMPLE_MP3_DIR, tmp_path)
        result = CliRunner().invoke(main, ["convert", rel_input, "-o", "out"])
        assert result.exit_code == 0, result.output
        data = _probe(tmp_path / "out" / "audiobook.m4b")
        assert [c["tags"]["title"] for c in data["chapters"]] == EXPECTED_TITLES


@requires_ffmpeg
@requires_mp4box
class TestConvertMp3Mp4box:
    def test_mp4box_method(self, tmp_path):
        out_dir = tmp_path / "out"
        result = CliRunner().invoke(
            main, ["convert", str(SAMPLE_MP3_DIR), "-o", str(out_dir), "--method", "mp4box"]
        )
        assert result.exit_code == 0, result.output
        data = _probe(out_dir / "audiobook.m4b")
        assert [c["tags"]["title"] for c in data["chapters"]] == EXPECTED_TITLES
