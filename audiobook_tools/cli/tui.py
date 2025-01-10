"""Terminal User Interface components using rich."""

import time
from pathlib import Path
from typing import List, Optional

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskID
from rich.prompt import Confirm, Prompt
from rich.table import Table

console = Console()


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
            cover_path = Prompt.ask("Cover art path")
            if Path(cover_path).is_file():
                metadata["cover"] = Path(cover_path)
                break
            console.print("[red]File not found. Please try again.[/red]")

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