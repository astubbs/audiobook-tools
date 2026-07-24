"""CLI entry point for audiobook-tools."""

from pathlib import Path

import click


@click.group(invoke_without_command=True)
@click.version_option(version="0.1.0")
@click.option(
    "--tui/--no-tui",
    default=True,
    help="Launch the interactive TUI when no command is given (default: enabled).",
)
@click.pass_context
def main(ctx, tui):
    """Convert CD rips and MP3 files into M4B audiobooks with chapter markers.

    Run with no command to launch an interactive guide, or use a subcommand
    (convert, merge, combine-cue, chapters, check-tools) directly.
    """
    if ctx.invoked_subcommand is not None:
        return

    if tui:
        from audiobook_tools.tui import display_welcome

        options = display_welcome()
        if options is None:
            click.echo("Cancelled.")
            return
        ctx.invoke(convert, **options)
    else:
        click.echo(ctx.get_help())


@main.command()
@click.argument("input_dir", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--output-dir",
    "-o",
    type=click.Path(path_type=Path),
    default=None,
    help="Output directory (default: ./out relative to input_dir).",
)
@click.option("--bitrate", "-b", default="64k", help="Audio bitrate (default: 64k).")
@click.option(
    "--method",
    type=click.Choice(["ffmpeg", "mp4box"]),
    default="ffmpeg",
    help="M4B creation method.",
)
@click.option("--title", "-t", default=None, help="Audiobook title.")
@click.option("--artist", "-a", default=None, help="Author/artist name.")
@click.option(
    "--cover", type=click.Path(exists=True, path_type=Path), default=None, help="Cover art image."
)
@click.option("--dry-run", is_flag=True, help="Show what would happen without making changes.")
@click.option("--resume", is_flag=True, help="Use existing intermediate files if present.")
def convert(input_dir, output_dir, bitrate, method, title, artist, cover, dry_run, resume):
    """Convert an audiobook directory to M4B.

    INPUT_DIR should contain CD subdirectories with FLAC+CUE or MP3 files.
    """
    import time

    from rich.console import Console
    from rich.panel import Panel

    from audiobook_tools.audio.encode import encode_to_aac
    from audiobook_tools.audio.m4b import create_m4b_ffmpeg, create_m4b_mp4box
    from audiobook_tools.audio.merge import (
        find_audio_files,
        merge_flac,
        merge_mp3,
        ordered_mp3_files,
    )
    from audiobook_tools.audio.probe import get_duration_seconds
    from audiobook_tools.chapters.ffmpeg import generate_ffmetadata
    from audiobook_tools.chapters.mp3 import generate_mp3_chapters
    from audiobook_tools.chapters.mp4box import generate_mp4box_chapters
    from audiobook_tools.cue.combiner import combine_cue_sheets

    console = Console()

    if output_dir is None:
        output_dir = Path("./out")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Detect input format. MP3 files are gathered in playback order so chapter
    # timestamps align with the concatenated audio.
    flac_files = find_audio_files(input_dir, "flac")
    mp3_files = [] if flac_files else ordered_mp3_files(input_dir)
    if flac_files:
        input_format = "flac"
    elif mp3_files:
        input_format = "mp3"
    else:
        raise click.ClickException(f"No FLAC or MP3 files found in {input_dir}")

    console.print(f"[bold]Detected format:[/bold] {input_format.upper()}")
    console.print(f"[bold]Output directory:[/bold] {output_dir}")

    start = time.monotonic()

    def step(number: int, message: str) -> None:
        console.print(f"\n[bold blue]Step {number}/4:[/bold blue] {message}")

    # Step 1: Merge audio files (sox/ffmpeg show their own progress)
    combined_audio = output_dir / f"combined.{input_format}"
    if resume and combined_audio.exists():
        step(1, f"Using existing {combined_audio.name}")
    else:
        step(1, f"Merging {input_format.upper()} files")
        if input_format == "flac":
            merge_flac(input_dir, combined_audio, dry_run=dry_run)
        else:
            merge_mp3(input_dir, combined_audio, dry_run=dry_run)

    if dry_run:
        console.print("\n[yellow]Dry run complete.[/yellow] No files were written.")
        return

    # Step 2: Generate chapter metadata
    step(2, "Generating chapter metadata")
    chapters_file = output_dir / "chapters.txt"
    if input_format == "flac":
        combined_cue = output_dir / "combined.cue"
        combine_cue_sheets(input_dir, combined_cue)
        if method == "ffmpeg":
            count = generate_ffmetadata(combined_cue, combined_audio, chapters_file)
        else:
            count = generate_mp4box_chapters(combined_cue, chapters_file)
    else:
        count = generate_mp3_chapters(mp3_files, chapters_file, method=method)
    console.print(f"  {count} chapters")

    # Step 3: Encode to AAC (ffmpeg shows its own progress)
    aac_file = output_dir / "audiobook.aac"
    if resume and aac_file.exists():
        step(3, f"Using existing {aac_file.name}")
    else:
        step(3, f"Encoding to AAC ({bitrate})")
        encode_to_aac(combined_audio, aac_file, bitrate=bitrate)

    # Step 4: Create M4B
    m4b_file = output_dir / "audiobook.m4b"
    step(4, "Creating M4B audiobook")
    if method == "ffmpeg":
        create_m4b_ffmpeg(
            aac_file, chapters_file, m4b_file, title=title, artist=artist, cover_path=cover
        )
    else:
        create_m4b_mp4box(aac_file, chapters_file, m4b_file)

    # Completion summary
    duration = get_duration_seconds(m4b_file)
    elapsed = time.monotonic() - start
    console.print(
        Panel(
            f"[bold green]Audiobook created[/bold green]\n\n"
            f"Output:   {m4b_file}\n"
            f"Duration: {duration / 3600:.1f} h  ({count} chapters)\n"
            f"Method:   {method}   Bitrate: {bitrate}\n"
            f"Elapsed:  {elapsed:.0f}s",
            title="✓ Done",
            expand=False,
        )
    )


@main.command("combine-cue")
@click.argument("input_dir", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    default="./out/combined.cue",
    help="Output CUE file path.",
)
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
@click.option(
    "--audio-file",
    type=click.Path(exists=True, path_type=Path),
    default=None,
    help="Audio file (required for ffmpeg format, to set last chapter end time).",
)
@click.option("--output", "-o", type=click.Path(path_type=Path), default="./out/chapters.txt")
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
