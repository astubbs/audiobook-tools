"""Command-line interface for audiobook tools.

Dependencies:
- click: Python package for creating beautiful command line interfaces with minimal code
- rich: Terminal formatting, progress bars and TUI elements
- dataclasses: Python standard library for creating data container classes
- pathlib: Python standard library for object-oriented filesystem paths
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

import click

from ..core.cue import CueProcessingError, CueProcessor
from ..core.processor import AudiobookMetadata, AudiobookProcessor, ProcessingOptions
from ..utils.audio import (
    AudioConfig,
    AudioProcessingError,
    convert_to_aac,
    create_m4b,
    create_m4b_mp4box,
    merge_flac_files,
    merge_mp3_files,
)
from . import tui as tui_module

# Configure logging
logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@dataclass
class CliContext:
    """Context object for CLI commands."""

    debug: bool = False
    use_tui: bool = True


@click.group(invoke_without_command=True)
@click.version_option(version="0.1.0")
@click.option("--debug/--no-debug", default=False, help="Enable debug logging")
@click.option(
    "--tui/--no-tui",
    default=True,
    is_flag=True,
    help="Enable/disable Terminal User Interface",
)
@click.pass_context
def cli(ctx, debug: bool, tui: bool):
    """Audiobook Tools - Process and convert audiobooks with chapter markers."""
    ctx.obj = CliContext(debug=debug, use_tui=tui)

    # Only set debug logging if --debug flag is used
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Debug mode enabled")

    logger.debug("CLI function called")
    logger.debug("Context: %s", ctx.obj)
    logger.debug("Invoked subcommand: %s", ctx.invoked_subcommand)
    logger.debug("Args: %s", ctx.args)

    # If no command is provided and --help is not used, show the welcome screen
    if ctx.invoked_subcommand is None and not any(
        arg in ["--help", "-h"] for arg in ctx.args
    ):
        logger.debug("Showing welcome screen")
        try:
            if ctx.obj.use_tui:
                logger.debug("Using TUI mode")
                logger.debug("About to call tui_module.display_welcome()")
                options = tui_module.display_welcome()
                logger.debug("Raw return value from display_welcome: %r", options)
                if options:
                    if isinstance(options, str):
                        logger.error(
                            "display_welcome returned a string instead of options dict: %r",
                            options,
                        )
                        raise click.ClickException(
                            "Invalid return value from welcome screen"
                        )
                    logger.debug("Invoking process command with options: %s", options)
                    ctx.invoke(process, **options)
                else:
                    logger.debug("No options returned from welcome screen")
            else:
                click.echo(ctx.get_help())
                ctx.exit(1)
        except Exception as e:
            logger.exception("Error in welcome screen")
            raise click.ClickException(f"Welcome screen error: {str(e)}")


@dataclass
class CliOptions:
    """Container for all CLI options."""

    input_dir: Path
    output_dir: Path
    output_format: str
    audio_config: AudioConfig
    metadata: AudiobookMetadata
    dry_run: bool
    interactive: bool
    resume: bool

    def to_processing_options(self) -> ProcessingOptions:
        """Convert to ProcessingOptions for the processor."""
        return ProcessingOptions(
            input_dir=self.input_dir,
            output_dir=self.output_dir,
            output_format=self.output_format,
            audio_config=self.audio_config,
            metadata=self.metadata,
            dry_run=self.dry_run,
            resume=self.resume,
        )


@dataclass
# pylint: disable=too-many-instance-attributes
# This class needs many attributes to fully represent all CLI options.
# Breaking it up would make the code less maintainable as these options are tightly coupled.
class ProcessCommandOptions:
    """Options for the process command."""

    input_dir: Path
    output_dir: Path
    output_format: str
    bitrate: str
    title: Optional[str]
    artist: Optional[str]
    cover: Optional[Path]
    dry_run: bool
    interactive: bool
    resume: bool

    def to_cli_options(self) -> CliOptions:
        """Convert to CliOptions."""
        audio_config = AudioConfig(bitrate=self.bitrate)
        metadata = AudiobookMetadata(
            title=self.title,
            artist=self.artist,
            cover_art=self.cover,
        )
        return CliOptions(
            input_dir=self.input_dir,
            output_dir=self.output_dir,
            output_format=self.output_format,
            audio_config=audio_config,
            metadata=metadata,
            dry_run=self.dry_run,
            interactive=self.interactive,
            resume=self.resume,
        )


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
# Audio config options
@click.option(
    "--bitrate",
    "-b",
    type=str,
    default="64k",
    help="Audio bitrate for encoding (default: 64k for spoken word)",
)
# Metadata options
@click.option(
    "--title",
    "-t",
    type=str,
    help="Audiobook title",
)
@click.option(
    "--artist",
    "-a",
    type=str,
    help="Audiobook artist/author",
)
@click.option(
    "--cover",
    "-c",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    help="Cover art image file",
)
# Processing options
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
@click.option(
    "--resume",
    "-r",
    is_flag=True,
    help="Resume from existing intermediate files if present",
)
@click.pass_context
# pylint: disable=too-many-arguments,too-many-locals
# Click requires each CLI option to be a separate argument.
# We mitigate this by immediately converting these into a proper options class.
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
    resume: bool,
):
    """Process an audiobook directory into a single file with chapters.

    INPUT_DIR is the directory containing the audiobook files (FLAC+CUE or MP3).
    """
    cmd_options = ProcessCommandOptions(
        input_dir=input_dir,
        output_dir=output_dir,
        output_format=output_format,
        bitrate=bitrate,
        title=title,
        artist=artist,
        cover=cover,
        dry_run=dry_run,
        interactive=interactive,
        resume=resume,
    )
    cli_options = cmd_options.to_cli_options()
    options = cli_options.to_processing_options()
    processor = create_processor(options)

    try:
        if ctx.obj.use_tui:
            tui_module.display_header("Processing Audiobook")

        audio_files = processor.find_audio_files()

        if interactive:
            if not confirm_processing(ctx, audio_files, output_dir):
                return

        process_audiobook(processor, options, audio_files, interactive=interactive)

    except (AudioProcessingError, CueProcessingError) as e:
        logger.error(str(e))
        raise click.ClickException(str(e))


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
                progress.start_task("Processing CUE files")
                output_file = processor.process_directory()
                progress.complete_task("Processing CUE files")

            tui_module.console.print()
            tui_module.console.print(
                f"[bold green]Successfully created combined CUE file:[/bold green] {output_file}"
            )
        else:
            output_file = processor.process_directory()
            click.echo(f"Successfully created combined CUE file: {output_file}")

    except CueProcessingError as e:
        logger.error(str(e))
        raise click.ClickException(str(e))


def create_processor(options: ProcessingOptions) -> AudiobookProcessor:
    """Create an AudiobookProcessor with the given processing options."""
    return AudiobookProcessor(options)


def confirm_processing(
    ctx: click.Context, audio_files: List[Path], output_dir: Path
) -> bool:
    """Confirm processing with the user, showing a summary of files and output directory."""
    if ctx.obj.use_tui:
        return tui_module.confirm_processing(audio_files, output_dir)
    click.echo("\nProcessing Summary:")
    for i, file in enumerate(audio_files, 1):
        size = file.stat().st_size / (1024 * 1024)
        click.echo(f"{i}. {file} ({size:.1f} MB)")
    click.echo(f"\nOutput directory: {output_dir}")
    return click.confirm("\nContinue with processing?")


def process_audiobook(
    processor: AudiobookProcessor,
    options: ProcessingOptions,
    audio_files: List[Path],
    interactive: bool = True,
):
    """Process the audiobook with or without progress tracking based on TUI usage."""
    if interactive:
        with tui_module.ProcessingProgress() as progress:
            if options.dry_run:
                progress.start_task("Dry run")
                processor.process()
                progress.complete_task("Dry run")
            else:
                process_with_progress(progress, options, audio_files)
    else:
        if options.dry_run:
            click.echo("Starting dry run...")
            processor.process()
            click.echo("Dry run completed successfully.")
        else:
            click.echo("Processing audiobook...")
            processor.process()
            click.echo(
                f"Successfully created audiobook: {options.output_dir / 'audiobook.m4b'}"
            )


def process_with_progress(
    progress: tui_module.ProcessingProgress,
    options: ProcessingOptions,
    audio_files: List[Path],
):
    """Process the audiobook with progress tracking, handling each step sequentially."""
    is_mp3 = audio_files[0].suffix.lower() == ".mp3"

    # Merge audio files
    progress.start_task(f"Merging {'MP3' if is_mp3 else 'FLAC'} files")
    if is_mp3:
        combined_audio = options.output_dir / "combined.mp3"
        if not (options.resume and combined_audio.exists()):
            merge_mp3_files(audio_files, combined_audio)
        else:
            logger.info("Using existing combined MP3 file: %s", combined_audio)
    else:
        combined_audio = options.output_dir / "combined.flac"
        if not (options.resume and combined_audio.exists()):
            merge_flac_files(audio_files, combined_audio)
        else:
            logger.info("Using existing combined FLAC file: %s", combined_audio)
    progress.complete_task(f"Merging {'MP3' if is_mp3 else 'FLAC'} files")

    # Process chapters
    progress.start_task("Processing chapters")
    if is_mp3:
        processor = AudiobookProcessor(options)
        chapters_file = processor.extract_chapters_from_filenames(audio_files)
    else:
        cue_processor = CueProcessor(options.input_dir, options.output_dir)
        chapters_file = cue_processor.process_directory()
    progress.complete_task("Processing chapters")

    progress.start_task("Converting audio")
    if options.output_format != "aac":
        aac_file = options.output_dir / "audiobook.aac"
        if not (options.resume and aac_file.exists()):
            convert_to_aac(combined_audio, aac_file, config=options.audio_config)
        else:
            logger.info("Using existing AAC file: %s", aac_file)
        output_file = options.output_dir / "audiobook.m4b"
        if options.output_format == "m4b-ffmpeg":
            create_m4b(
                aac_file,
                output_file,
                chapters_file=chapters_file,
                metadata=options.metadata,
            )
        else:
            create_m4b_mp4box(aac_file, output_file, chapters_file=chapters_file)
    else:
        output_file = options.output_dir / "audiobook.aac"
        convert_to_aac(combined_audio, output_file, config=options.audio_config)
    progress.complete_task("Converting audio")


def main():
    """Main entry point for the CLI."""
    try:
        logger.debug("Starting main function")
        cli.main(args=None, prog_name=None)
    except Exception as e:
        logger.exception("Unexpected error in main function")
        raise click.ClickException(str(e))
