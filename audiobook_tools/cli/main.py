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
       --format m4b-ffmpeg \\
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

The CLI is built using Click and provides:
- Command grouping and nesting
- Automatic help text generation
- Type checking and validation of inputs
- Proper error handling and user feedback
"""
import logging
from pathlib import Path
import click

from ..core.cue import CueProcessor, CueProcessingError
from ..core.processor import AudiobookProcessor, ProcessingOptions
from ..utils.audio import AudioProcessingError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@click.group()
@click.option(
    '--debug/--no-debug',
    default=False,
    help='Enable debug logging'
)
def cli(debug):
    """Audiobook Tools - Process and convert audiobooks with chapter markers."""
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)

@cli.command()
@click.argument(
    'input_dir',
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path)
)
@click.argument(
    'output_dir',
    type=click.Path(file_okay=False, dir_okay=True, path_type=Path)
)
def combine_cue(input_dir: Path, output_dir: Path):
    """Combine multiple CUE sheets into a single file.
    
    INPUT_DIR is the directory containing the audiobook files and CUE sheets.
    OUTPUT_DIR is where the combined CUE file will be written.
    """
    try:
        processor = CueProcessor(input_dir, output_dir)
        output_file = processor.process_directory()
        click.echo(f"Successfully created combined CUE file: {output_file}")
    except CueProcessingError as e:
        logger.error(str(e))
        raise click.ClickException(str(e))

@cli.command()
@click.argument(
    'input_dir',
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path)
)
@click.option(
    '--output-dir', '-o',
    type=click.Path(file_okay=False, dir_okay=True, path_type=Path),
    default=Path('out'),
    help='Output directory for processed files'
)
@click.option(
    '--format', '-f',
    type=click.Choice(['m4b-ffmpeg', 'm4b-mp4box', 'aac']),
    default='m4b-ffmpeg',
    help='Output format and processing method'
)
@click.option(
    '--bitrate', '-b',
    type=str,
    default='64k',
    help='Audio bitrate for encoding (default: 64k for spoken word)'
)
@click.option(
    '--title', '-t',
    type=str,
    help='Audiobook title'
)
@click.option(
    '--artist', '-a',
    type=str,
    help='Audiobook artist/author'
)
@click.option(
    '--cover', '-c',
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    help='Cover art image file'
)
@click.option(
    '--dry-run', '-d',
    is_flag=True,
    help='Show what would be done without making changes'
)
def process(
    input_dir: Path,
    output_dir: Path,
    format: str,
    bitrate: str,
    title: str,
    artist: str,
    cover: Path,
    dry_run: bool
):
    """Process an audiobook directory into a single file with chapters.
    
    INPUT_DIR is the directory containing the audiobook files and CUE sheets.
    """
    try:
        options = ProcessingOptions(
            input_dir=input_dir,
            output_dir=output_dir,
            format=format,
            bitrate=bitrate,
            title=title,
            artist=artist,
            cover_art=cover,
            dry_run=dry_run
        )
        
        processor = AudiobookProcessor(options)
        output_file = processor.process()
        
        if dry_run:
            click.echo("Dry run completed successfully. No files were modified.")
        else:
            click.echo(f"Successfully created audiobook: {output_file}")
            
    except (AudioProcessingError, CueProcessingError) as e:
        logger.error(str(e))
        raise click.ClickException(str(e))

def main():
    """Main entry point for the CLI."""
    try:
        cli()
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise click.ClickException(str(e)) 