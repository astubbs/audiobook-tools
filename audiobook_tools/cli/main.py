"""Command-line interface for audiobook tools.

This module provides the command-line interface for the audiobook tools package.
It offers two main commands:

1. process: Convert an audiobook directory to M4B/AAC format
   ```bash
   # Basic usage
   audiobook-tools process ./audiobook-dir
   
   # Advanced usage with all options
   audiobook-tools process ./audiobook-dir \\
       --output-dir ./out \\
       --output-format m4b-ffmpeg \\
       --bitrate 64k \\
       --title "Book Title" \\
       --artist "Author Name" \\
       --cover cover.jpg
   ```

2. combine-cue: Just combine CUE sheets (useful for manual processing)
   ```bash
   audiobook-tools combine-cue ./audiobook-dir ./out
   ```

Common Options:
- --debug: Enable debug logging
- --dry-run: Show what would be done without making changes
- --no-tui: Disable the Terminal User Interface
- --no-interactive: Disable interactive prompts

The CLI is built using Click and provides:
- Command grouping and nesting
- Automatic help text generation
- Type checking and validation of inputs
- Proper error handling and user feedback
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import click

from ..core.cue import CueProcessingError, CueProcessor
from ..core.processor import AudiobookProcessor, ProcessingOptions
from ..utils.audio import AudioProcessingError
from . import tui as tui_module

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class CliContext:
    """Context object for CLI commands."""
    debug: bool = False
    use_tui: bool = True


@click.group(invoke_without_command=True)
@click.option("--debug/--no-debug", default=False, help="Enable debug logging")
@click.option("--tui/--no-tui", default=True, help="Enable/disable Terminal User Interface")
@click.pass_context
def cli(ctx, debug: bool, tui: bool):
    """Audiobook Tools - Process and convert audiobooks with chapter markers."""
    ctx.obj = CliContext(debug=debug, use_tui=tui)
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Debug mode enabled")

    # If no command is provided and --help is not used, show the welcome screen
    if ctx.invoked_subcommand is None and not any(arg in ['--help', '-h'] for arg in ctx.args):
        logger.debug("Showing welcome screen")
        if ctx.obj.use_tui:
            logger.debug("Using TUI mode")
            options = tui_module.display_welcome()
            if options:
                logger.debug("Options from welcome screen: %s", options)
                ctx.invoke(process, **options)
        else:
            logger.debug("Using CLI mode")
            click.echo(ctx.get_help())
            ctx.exit(1)


@cli.command()
@click.argument(
    "input_dir",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
)
@click.argument(
    "output_dir", type=click.Path(file_okay=False, dir_okay=True, path_type=Path)
)
@click.pass_context
def combine_cue(ctx, input_dir: Path, output_dir: Path):
    """Combine multiple CUE sheets into a single file.

    INPUT_DIR is the directory containing the audiobook files and CUE sheets.
    OUTPUT_DIR is where the combined CUE file will be written.
    """
    try:
        if ctx.obj.use_tui:
            tui_module.display_header("Combining CUE Sheets")

        processor = CueProcessor(input_dir, output_dir)
        
        if ctx.obj.use_tui:
            with tui_module.ProcessingProgress() as progress:
                task = progress.start_task("Processing CUE files")
                output_file = processor.process_directory()
                progress.complete_task("Processing CUE files")

            tui_module.console.print()
            tui_module.console.print(
                "[bold green]Successfully created combined CUE file:[/bold green] "
                + str(output_file)
            )
        else:
            output_file = processor.process_directory()
            click.echo("Successfully created combined CUE file: %s" % output_file)

    except CueProcessingError as e:
        logger.error(str(e))
        raise click.ClickException(str(e))


@cli.command()
@click.argument(
    "input_dir",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
)
@click.option(
    "--output-dir",
    "-o",
    type=click.Path(file_okay=False, dir_okay=True, path_type=Path),
    default=Path("out"),
    help="Output directory for processed files",
)
@click.option(
    "--output-format",
    "-f",
    type=click.Choice(["m4b-ffmpeg", "m4b-mp4box", "aac"]),
    default="m4b-ffmpeg",
    help="Output format and processing method",
)
@click.option(
    "--bitrate",
    "-b",
    type=str,
    default="64k",
    help="Audio bitrate for encoding (default: 64k for spoken word)",
)
@click.option("--title", "-t", type=str, help="Audiobook title")
@click.option("--artist", "-a", type=str, help="Audiobook artist/author")
@click.option(
    "--cover",
    "-c",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    help="Cover art image file",
)
@click.option(
    "--dry-run",
    "-d",
    is_flag=True,
    help="Show what would be done without making changes",
)
@click.option(
    "--interactive/--no-interactive",
    "-i/-n",
    default=True,
    help="Enable/disable interactive mode",
)
@click.pass_context
def process(
    ctx,
    input_dir: Path,
    output_dir: Path,
    output_format: str,
    bitrate: str,
    title: Optional[str],
    artist: Optional[str],
    cover: Optional[Path],
    dry_run: bool,
    interactive: bool,
):
    """Process an audiobook directory into a single file with chapters.

    INPUT_DIR is the directory containing the audiobook files and CUE sheets.
    """
    try:
        if ctx.obj.use_tui:
            tui_module.display_header("Processing Audiobook")

        # Create processor to find files
        options = ProcessingOptions(
            input_dir=input_dir,
            output_dir=output_dir,
            output_format=output_format,
            bitrate=bitrate,
            title=title,
            artist=artist,
            cover_art=cover,
            dry_run=dry_run,
        )
        processor = AudiobookProcessor(options)

        # Find FLAC files
        flac_files = processor.find_flac_files()

        # In interactive mode, prompt for missing metadata
        if interactive and not dry_run and not (title and artist):
            if ctx.obj.use_tui:
                metadata = tui_module.prompt_metadata()
            else:
                metadata = {
                    "title": click.prompt("Title", default=""),
                    "artist": click.prompt("Artist/Author", default=""),
                }
                if click.confirm("Add cover art?", default=False):
                    while True:
                        cover_path = click.prompt("Cover art path")
                        if Path(cover_path).is_file():
                            metadata["cover"] = Path(cover_path)
                            break
                        click.echo("File not found. Please try again.")

            options.title = title or metadata.get("title")
            options.artist = artist or metadata.get("artist")
            options.cover_art = cover or metadata.get("cover")

        # Show summary and confirm
        if interactive:
            if ctx.obj.use_tui:
                if not tui_module.confirm_processing(flac_files, output_dir):
                    tui_module.console.print("[yellow]Operation cancelled.[/yellow]")
                    return
            else:
                click.echo("\nProcessing Summary:")
                for i, file in enumerate(flac_files, 1):
                    size = file.stat().st_size / (1024 * 1024)
                    click.echo(f"{i}. {file} ({size:.1f} MB)")
                click.echo(f"\nOutput directory: {output_dir}")
                if not click.confirm("\nContinue with processing?"):
                    click.echo("Operation cancelled.")
                    return

        if ctx.obj.use_tui:
            # Process files with progress tracking
            with tui_module.ProcessingProgress() as progress:
                if dry_run:
                    progress.start_task("Dry run")
                    output_file = processor.process()
                    progress.complete_task("Dry run")
                else:
                    # Merge FLAC files
                    task = progress.start_task("Merging FLAC files")
                    processor.process()
                    progress.complete_task("Merging FLAC files")

                    # Process CUE sheets
                    task = progress.start_task("Processing CUE sheets")
                    processor.process()
                    progress.complete_task("Processing CUE sheets")

                    # Convert audio
                    task = progress.start_task("Converting audio")
                    output_file = processor.process()
                    progress.complete_task("Converting audio")

            if dry_run:
                tui_module.console.print("[green]Dry run completed successfully.[/green]")
            else:
                tui_module.console.print(
                    "[bold green]Successfully created audiobook:[/bold green] "
                    + str(output_file)
                )
        else:
            # Process without progress tracking
            if dry_run:
                click.echo("Starting dry run...")
                output_file = processor.process()
                click.echo("Dry run completed successfully.")
            else:
                click.echo("Merging FLAC files...")
                processor.process()
                click.echo("Processing CUE sheets...")
                processor.process()
                click.echo("Converting audio...")
                output_file = processor.process()
                click.echo("Successfully created audiobook: %s" % output_file)

    except (AudioProcessingError, CueProcessingError) as e:
        logger.error(str(e))
        raise click.ClickException(str(e))


def main():
    """Main entry point for the CLI."""
    try:
        cli(obj={})
    except Exception as e:
        logger.error("Unexpected error: %s", e)
        raise click.ClickException(str(e))