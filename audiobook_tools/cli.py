"""CLI entry point for audiobook-tools."""

from pathlib import Path

import click


@click.group()
@click.version_option(version="0.1.0")
def main():
    """Convert CD rips and MP3 files into M4B audiobooks with chapter markers."""


@main.command()
@click.argument("input_dir", type=click.Path(exists=True, path_type=Path))
@click.option("--output-dir", "-o", type=click.Path(path_type=Path), default=None,
              help="Output directory (default: ./out relative to input_dir).")
@click.option("--bitrate", "-b", default="64k", help="Audio bitrate (default: 64k).")
@click.option("--method", type=click.Choice(["ffmpeg", "mp4box"]), default="ffmpeg",
              help="M4B creation method.")
@click.option("--title", "-t", default=None, help="Audiobook title.")
@click.option("--artist", "-a", default=None, help="Author/artist name.")
@click.option("--cover", type=click.Path(exists=True, path_type=Path), default=None,
              help="Cover art image.")
@click.option("--dry-run", is_flag=True, help="Show what would happen without making changes.")
@click.option("--resume", is_flag=True,
              help="Use existing intermediate files if present.")
def convert(input_dir, output_dir, bitrate, method, title, artist, cover, dry_run, resume):
    """Convert an audiobook directory to M4B.

    INPUT_DIR should contain CD subdirectories with FLAC+CUE or MP3 files.
    """
    from audiobook_tools.audio.encode import encode_to_aac
    from audiobook_tools.audio.m4b import create_m4b_ffmpeg, create_m4b_mp4box
    from audiobook_tools.audio.merge import find_audio_files, merge_flac, merge_mp3
    from audiobook_tools.audio.probe import get_duration_seconds
    from audiobook_tools.chapters.ffmpeg import generate_ffmetadata
    from audiobook_tools.chapters.mp4box import generate_mp4box_chapters
    from audiobook_tools.cue.combiner import combine_cue_sheets

    if output_dir is None:
        output_dir = Path("./out")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Detect input format
    flac_files = find_audio_files(input_dir, "flac")
    mp3_files = list(input_dir.rglob("*.mp3"))
    if flac_files:
        input_format = "flac"
    elif mp3_files:
        input_format = "mp3"
    else:
        raise click.ClickException(f"No FLAC or MP3 files found in {input_dir}")

    click.echo(f"Detected format: {input_format.upper()}")
    click.echo(f"Output directory: {output_dir}")

    if dry_run:
        click.echo("\n--- DRY RUN ---")

    # Step 1: Merge audio files
    combined_audio = output_dir / f"combined.{input_format}"
    if resume and combined_audio.exists():
        click.echo(f"\nStep 1: Using existing {combined_audio}")
    else:
        click.echo(f"\nStep 1: Merging {input_format.upper()} files...")
        if input_format == "flac":
            merge_flac(input_dir, combined_audio, dry_run=dry_run)
        else:
            merge_mp3(input_dir, combined_audio, dry_run=dry_run)

    if dry_run:
        click.echo("\nDry run complete.")
        return

    # Step 2: Process chapters
    click.echo("\nStep 2: Generating chapter metadata...")
    if input_format == "flac":
        combined_cue = output_dir / "combined.cue"
        combine_cue_sheets(input_dir, combined_cue)

        if method == "ffmpeg":
            chapters_file = output_dir / "chapters.txt"
            count = generate_ffmetadata(combined_cue, combined_audio, chapters_file)
        else:
            chapters_file = output_dir / "chapters.txt"
            count = generate_mp4box_chapters(combined_cue, chapters_file)
        click.echo(f"Generated {count} chapters")
    else:
        # MP3: generate chapters from filenames (Phase 7)
        chapters_file = output_dir / "chapters.txt"
        count = _generate_mp3_chapters(mp3_files, chapters_file)
        click.echo(f"Generated {count} chapters from filenames")

    # Step 3: Encode to AAC
    aac_file = output_dir / "audiobook.aac"
    if resume and aac_file.exists():
        click.echo(f"\nStep 3: Using existing {aac_file}")
    else:
        click.echo(f"\nStep 3: Encoding to AAC ({bitrate})...")
        encode_to_aac(combined_audio, aac_file, bitrate=bitrate)

    # Step 4: Create M4B
    m4b_file = output_dir / "audiobook.m4b"
    click.echo("\nStep 4: Creating M4B audiobook...")
    if method == "ffmpeg":
        create_m4b_ffmpeg(aac_file, chapters_file, m4b_file,
                          title=title, artist=artist, cover_path=cover)
    else:
        create_m4b_mp4box(aac_file, chapters_file, m4b_file)

    duration = get_duration_seconds(m4b_file)
    click.echo(f"\nDone! {m4b_file} ({duration / 3600:.1f} hours)")


@main.command("combine-cue")
@click.argument("input_dir", type=click.Path(exists=True, path_type=Path))
@click.option("--output", "-o", type=click.Path(path_type=Path),
              default="./out/combined.cue", help="Output CUE file path.")
def combine_cue(input_dir, output):
    """Combine multiple CUE sheets into one."""
    from audiobook_tools.cue.combiner import combine_cue_sheets
    combine_cue_sheets(input_dir, Path(output))


@main.command()
@click.argument("input_dir", type=click.Path(exists=True, path_type=Path))
@click.option("--output-dir", "-o", type=click.Path(path_type=Path), default="./out")
@click.option("--dry-run", is_flag=True)
def merge(input_dir, output_dir, dry_run):
    """Merge audio files from CD directories into a single file."""
    from audiobook_tools.audio.merge import find_audio_files, merge_flac, merge_mp3

    output_dir = Path(output_dir)
    flac_files = find_audio_files(input_dir, "flac")
    if flac_files:
        merge_flac(input_dir, output_dir / "combined.flac", dry_run=dry_run)
    else:
        merge_mp3(input_dir, output_dir / "combined.mp3", dry_run=dry_run)


@main.command()
@click.argument("cue_file", type=click.Path(exists=True, path_type=Path))
@click.option("--format", "fmt", type=click.Choice(["ffmpeg", "mp4box"]), default="ffmpeg")
@click.option("--audio-file", type=click.Path(exists=True, path_type=Path), default=None,
              help="Audio file (required for ffmpeg format, to set last chapter end time).")
@click.option("--output", "-o", type=click.Path(path_type=Path),
              default="./out/chapters.txt")
def chapters(cue_file, fmt, audio_file, output):
    """Generate a chapter file from a CUE sheet."""
    from audiobook_tools.chapters.ffmpeg import generate_ffmetadata
    from audiobook_tools.chapters.mp4box import generate_mp4box_chapters

    output = Path(output)
    if fmt == "ffmpeg":
        if not audio_file:
            raise click.ClickException("--audio-file is required for ffmpeg format")
        count = generate_ffmetadata(cue_file, audio_file, output)
    else:
        count = generate_mp4box_chapters(cue_file, output)

    click.echo(f"Generated {count} chapters -> {output}")


@main.command("check-tools")
def check_tools():
    """Check that required external tools are installed."""
    from audiobook_tools.utils.external import check_tool

    tools = {
        "ffmpeg": "Audio conversion and M4B creation",
        "ffprobe": "Audio file inspection (usually bundled with ffmpeg)",
        "sox": "FLAC file merging",
        "MP4Box": "Alternative M4B creation (optional)",
    }
    all_ok = True
    for tool, description in tools.items():
        found = check_tool(tool)
        status = "OK" if found else "MISSING"
        click.echo(f"  {tool:10s} {status:8s}  {description}")
        if not found and tool != "MP4Box":
            all_ok = False

    if not all_ok:
        raise SystemExit(1)


def _generate_mp3_chapters(mp3_files: list[Path], output_path: Path) -> int:
    """Generate FFmpeg chapter metadata from MP3 filenames.

    Extracts chapter titles from filenames like:
      01 - Chapter One.mp3
      CD1 - 01 - Introduction.mp3
    """
    import re
    from audiobook_tools.audio.probe import get_duration_ms

    mp3_files = sorted(mp3_files)
    chapters: list[tuple[int, str]] = []
    current_ms = 0

    for f in mp3_files:
        name = f.stem
        # Try to extract chapter title from filename
        # Patterns: "01 - Title", "CD1 - 01 - Title", just "Title"
        match = re.search(r"(?:\d+\s*-\s*)?(?:CD\d+\s*-\s*)?(\d+\s*-\s*)?(.+)", name)
        if match:
            title = match.group(2).strip()
        else:
            title = name

        chapters.append((current_ms, title))
        current_ms += get_duration_ms(f)

    if not chapters:
        return 0

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as out:
        out.write(";FFMETADATA1\n\n")
        for i, (start_ms, title) in enumerate(chapters):
            end_ms = chapters[i + 1][0] if i < len(chapters) - 1 else current_ms
            out.write("[CHAPTER]\n")
            out.write("TIMEBASE=1/1000\n")
            out.write(f"START={start_ms}\n")
            out.write(f"END={end_ms}\n")
            out.write(f"title={title}\n\n")

    return len(chapters)
