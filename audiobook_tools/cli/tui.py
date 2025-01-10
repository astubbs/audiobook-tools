"""Terminal User Interface components using rich."""

import logging
import time
from pathlib import Path
from typing import List, Optional

import questionary
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskID
from rich.prompt import Confirm, Prompt
from rich.table import Table

console = Console()
logger = logging.getLogger(__name__)


def browse_directory(message: str, default: str = ".") -> Optional[Path]:
    """Browse for a directory using questionary's path autocomplete.
    
    Args:
        message: The prompt message to display
        default: The default directory to start in
    
    Returns:
        Selected directory path or None if cancelled
    """
    try:
        # Ensure default directory exists
        current = Path(default).resolve()
        current.mkdir(parents=True, exist_ok=True)
        
        # Show current directory contents
        try:
            dirs = [d for d in current.iterdir() if d.is_dir()]
            if dirs:
                console.print("\n[dim]Available directories:[/dim]")
                for d in sorted(dirs):
                    console.print(f"[dim]  {d.name}/[/dim]")
                console.print()
        except OSError:
            # Handle case where directory listing fails
            pass

        console.print("[dim]Navigation: Use Tab to autocomplete, ↑/↓ to view history, Enter to select[/dim]")
        path = questionary.path(
            message,
            default=str(current),
            only_directories=True,
            validate=lambda p: True  # Allow non-existent directories
        ).ask()
        
        if path:
            selected = Path(path)
            selected.mkdir(parents=True, exist_ok=True)
            return selected
        return None
    except KeyboardInterrupt:
        return None


def display_welcome():
    """Display the welcome screen and guide user through initial choices."""
    console.print()
    console.print(Panel(
        "[bold blue]Welcome to Audiobook Tools[/bold blue]\n\n"
        "This tool helps you process audiobooks from CD rips (FLAC+CUE) into M4B format.\n"
        "It will guide you through the process step by step.",
        title="🎧 Audiobook Tools",
        subtitle="Press Ctrl+C at any time to exit",
    ), justify="center")
    console.print()

    # Get input directory with browser
    while True:
        input_dir = browse_directory(
            "[bold]Select your audiobook directory[/bold]\n"
            "This should be the directory containing your CD folders with FLAC and CUE files"
        )
        
        if input_dir is None:  # User cancelled
            return None
            
        if not input_dir.exists():
            console.print("[red]Directory not found. Please try again.[/red]")
            continue
            
        flac_files = list(input_dir.rglob("*.flac"))
        if not flac_files:
            console.print("[red]No FLAC files found in this directory. Please check the path.[/red]")
            if not Confirm.ask("Try another directory?"):
                return None
            continue
            
        break

    # Show found files
    display_files(flac_files, "Found Audio Files")

    # Get output directory with browser
    default_output = str(input_dir.parent / "out")
    output_dir = browse_directory(
        "[bold]Select output directory[/bold]",
        default=default_output
    )
    
    if output_dir is None:  # User cancelled
        return None

    # Get format
    format_choices = {
        "1": ("m4b-ffmpeg", "M4B using FFmpeg (recommended)"),
        "2": ("m4b-mp4box", "M4B using MP4Box"),
        "3": ("aac", "AAC audio only"),
    }
    
    console.print("\n[bold]Choose output format:[/bold]")
    for key, (_, desc) in format_choices.items():
        console.print(f"{key}. {desc}")
    
    format_choice = Prompt.ask(
        "Enter your choice",
        choices=list(format_choices.keys()),
        default="1"
    )
    output_format = format_choices[format_choice][0]

    # Get metadata if creating M4B
    metadata = {}
    if output_format.startswith("m4b"):
        metadata = prompt_metadata()

    result = {
        "input_dir": input_dir,
        "output_dir": output_dir,
        "output_format": output_format,
        "bitrate": "64k",  # Default bitrate
        "dry_run": False,  # Default to actual processing
        "interactive": True,  # Default to interactive mode
        **metadata
    }
    
    logger.debug("Returning options: %s", result)
    return result


def display_header(title: str) -> None:
    """Display a header with the given title."""
    console.print()
    console.print(Panel(title, style="bold blue"), justify="center")
    console.print()


def display_files(files: List[Path], title: str = "Found Files") -> None:
    """Display a list of files in a table."""
    table = Table(title=title, show_header=True, header_style="bold magenta")
    table.add_column("Number", style="dim")
    table.add_column("File", style="cyan")
    table.add_column("Size", justify="right", style="green")

    for i, file in enumerate(files, 1):
        size = file.stat().st_size / (1024 * 1024)  # Convert to MB
        table.add_row(str(i), str(file), f"{size:.1f} MB")

    console.print(table)
    console.print()


def create_progress() -> Progress:
    """Create a progress bar with spinner and status."""
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console,
    )


class ProcessingProgress:
    """Context manager for tracking audiobook processing progress."""

    def __init__(self):
        self.progress = create_progress()
        self.tasks = {}

    def __enter__(self) -> "ProcessingProgress":
        self.progress.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.progress.__exit__(exc_type, exc_val, exc_tb)

    def add_task(self, description: str, total: Optional[float] = None) -> TaskID:
        """Add a new task to the progress bar."""
        return self.progress.add_task(description, total=total or 100)

    def update(self, task_id: TaskID, advance: float = 1, **kwargs) -> None:
        """Update a task's progress."""
        self.progress.update(task_id, advance=advance, **kwargs)

    def start_task(self, name: str) -> TaskID:
        """Start a new processing task."""
        task_id = self.add_task(f"[bold blue]{name}...")
        self.tasks[name] = task_id
        return task_id

    def complete_task(self, name: str) -> None:
        """Mark a task as complete."""
        if name in self.tasks:
            self.update(
                self.tasks[name],
                completed=100,
                description=f"[bold green]{name} ✓",
            )
            time.sleep(0.5)  # Give user time to see completion

    def fail_task(self, name: str, error: str) -> None:
        """Mark a task as failed."""
        if name in self.tasks:
            self.update(
                self.tasks[name],
                completed=100,
                description=f"[bold red]{name} ✗ ({error})",
            )


def prompt_metadata() -> dict:
    """Prompt user for audiobook metadata."""
    console.print()
    console.print("[bold]Please enter audiobook metadata:[/bold]")
    console.print()

    metadata = {
        "title": Prompt.ask("Title", default=""),
        "artist": Prompt.ask("Artist/Author", default=""),
    }

    if Prompt.ask("Add cover art?", choices=["y", "n"], default="n") == "y":
        while True:
            cover_path = questionary.path(
                "Select cover art image",
                validate=lambda p: Path(p).is_file() or "Please select a valid file"
            ).ask()
            
            if cover_path:
                metadata["cover"] = Path(cover_path)
                break
            else:  # User cancelled
                if not Confirm.ask("Try another file?"):
                    break

    console.print()
    return metadata


def confirm_processing(files: List[Path], output_dir: Path) -> bool:
    """Ask user to confirm processing."""
    console.print("[bold]Processing Summary:[/bold]")
    console.print()
    display_files(files)
    console.print(f"Output directory: [cyan]{output_dir}[/cyan]")
    console.print()
    return Confirm.ask("Continue with processing?") 