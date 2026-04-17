"""Merge multiple audio files into a single file."""

import re
import subprocess
from pathlib import Path

from audiobook_tools.audio.probe import get_duration_seconds
from audiobook_tools.utils.external import require_tool


def find_audio_files(input_dir: Path, extension: str = "flac") -> list[Path]:
    """Find audio files under input_dir, sorted by CD number.

    Looks for files matching *CD*.{extension} pattern.
    """
    pattern = f"*.{extension}"
    files = []
    for f in input_dir.rglob(pattern):
        if re.search(r"CD\d+", str(f)):
            files.append(f)

    files.sort(key=lambda p: _cd_sort_key(p))
    return files


def merge_flac(
    input_dir: Path,
    output_path: Path,
    dry_run: bool = False,
) -> list[Path]:
    """Merge FLAC files into a single combined FLAC using sox.

    Args:
        input_dir: Directory containing CD subdirectories with FLAC files.
        output_path: Where to write the combined FLAC file.
        dry_run: If True, only show what would happen.

    Returns:
        List of input files that were (or would be) merged.
    """
    require_tool("sox")

    files = find_audio_files(input_dir, "flac")
    if not files:
        raise FileNotFoundError(f"No FLAC files with CD pattern found in {input_dir}")

    print(f"\nFiles to combine ({len(files)}):")
    for i, f in enumerate(files, 1):
        duration = get_duration_seconds(f)
        hours = duration / 3600
        print(f"  {i}. {f.name}  ({hours:.2f} hours)")

    if dry_run:
        print("\nDry run complete. No files were merged.")
        return files

    output_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = ["sox", "--show-progress"] + [str(f) for f in files] + [str(output_path)]
    subprocess.run(cmd, check=True)

    duration = get_duration_seconds(output_path)
    print(f"\nCombined file: {output_path} ({duration / 3600:.2f} hours)")
    return files


def merge_mp3(
    input_dir: Path,
    output_path: Path,
    dry_run: bool = False,
) -> list[Path]:
    """Merge MP3 files into a single combined file using ffmpeg concat.

    Args:
        input_dir: Directory containing MP3 files.
        output_path: Where to write the combined file.
        dry_run: If True, only show what would happen.

    Returns:
        List of input files that were (or would be) merged.
    """
    require_tool("ffmpeg")

    files = find_audio_files(input_dir, "mp3")
    if not files:
        # Also try flat directory (files sorted by name)
        files = sorted(input_dir.rglob("*.mp3"))
    if not files:
        raise FileNotFoundError(f"No MP3 files found in {input_dir}")

    print(f"\nFiles to combine ({len(files)}):")
    for i, f in enumerate(files, 1):
        print(f"  {i}. {f.name}")

    if dry_run:
        print("\nDry run complete. No files were merged.")
        return files

    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Create concat list file for ffmpeg
    concat_list = output_path.parent / "concat_list.txt"
    with open(concat_list, "w", encoding="utf-8") as f:
        for mp3 in files:
            f.write(f"file '{mp3}'\n")

    cmd = [
        "ffmpeg",
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(concat_list),
        "-c",
        "copy",
        str(output_path),
    ]
    subprocess.run(cmd, check=True)
    concat_list.unlink()

    print(f"\nCombined file: {output_path}")
    return files


def _cd_sort_key(path: Path) -> int:
    match = re.search(r"CD(\d+)", str(path))
    return int(match.group(1)) if match else 0
