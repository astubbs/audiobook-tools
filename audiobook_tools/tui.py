"""Interactive terminal UI for audiobook-tools, built on rich + questionary.

Running ``audiobook`` with no subcommand launches :func:`display_welcome`, which
guides the user through selecting input/output directories, an output method, and
metadata, then hands the collected options to the ``convert`` command.
"""

from pathlib import Path

import questionary
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table

console = Console()


def browse_directory(message: str, default: str = ".") -> Path | None:
    """Browse for a directory using questionary's path autocomplete.

    Returns the selected directory (created if missing), or None if cancelled.
    """
    try:
        current = Path(default).resolve()
        current.mkdir(parents=True, exist_ok=True)

        try:
            dirs = sorted(d for d in current.iterdir() if d.is_dir())
            if dirs:
                console.print("\n[dim]Available directories:[/dim]")
                for d in dirs:
                    console.print(f"[dim]  {d.name}/[/dim]")
                console.print()
        except OSError:
            pass

        console.print(
            "[dim]Navigation: Tab to autocomplete, up/down for history, Enter to select[/dim]"
        )
        path = questionary.path(
            message,
            default=str(current),
            only_directories=True,
            validate=lambda _p: True,  # allow non-existent directories
        ).ask()

        if path:
            selected = Path(path)
            selected.mkdir(parents=True, exist_ok=True)
            return selected
        return None
    except KeyboardInterrupt:
        return None


def display_files(files: list[Path], title: str = "Found Files") -> None:
    """Render a list of files as a rich table with sizes in MB."""
    table = Table(title=title, show_header=True, header_style="bold magenta")
    table.add_column("Number", style="dim")
    table.add_column("File", style="cyan")
    table.add_column("Size", justify="right", style="green")

    for i, file in enumerate(files, 1):
        size_mb = file.stat().st_size / (1024 * 1024)
        table.add_row(str(i), str(file), f"{size_mb:.1f} MB")

    console.print(table)
    console.print()


def handle_no_audio_files(directory: Path) -> bool:
    """Report that no audio was found; return True if the user wants to retry."""
    console.print(f"[red]No FLAC or MP3 files found in {directory}. Please check the path.[/red]")
    return Confirm.ask("Try another directory?", default=True)


def prompt_metadata() -> dict[str, str | Path | None]:
    """Prompt for audiobook metadata (title, artist, optional cover art)."""
    console.print("\n[bold]Please enter audiobook metadata:[/bold]\n")

    title = Prompt.ask("Title", default="").strip()
    artist = Prompt.ask("Artist/Author", default="").strip()
    metadata: dict[str, str | Path | None] = {
        "title": title or None,
        "artist": artist or None,
    }

    if Prompt.ask("Add cover art?", choices=["y", "n"], default="n") == "y":
        while True:
            cover = questionary.path(
                "Select cover art image",
                validate=lambda p: Path(p).is_file() or "Please select a valid file",
            ).ask()
            if cover:
                metadata["cover"] = Path(cover)
                break
            if not Confirm.ask("Try another file?"):
                break

    console.print()
    return metadata


def confirm_processing(files: list[Path], output_dir: Path) -> bool:
    """Show a summary and ask the user to confirm before processing."""
    console.print("[bold]Processing summary:[/bold]\n")
    display_files(files)
    console.print(f"Output directory: [cyan]{output_dir}[/cyan]\n")
    return Confirm.ask("Continue with processing?", default=True)


def display_welcome() -> dict | None:
    """Guide the user through initial choices for a conversion.

    Returns a dict of options keyed to the ``convert`` command's parameters,
    or None if the user cancelled.
    """
    console.print()
    console.print(
        Panel(
            "[bold blue]Welcome to Audiobook Tools[/bold blue]\n\n"
            "Convert audiobooks from:\n"
            "- CD rips (FLAC+CUE format)\n"
            "- MP3 files with chapter info in filenames\n\n"
            "This will guide you through the process step by step.",
            title="🎧 Audiobook Tools",
            subtitle="Press Ctrl+C at any time to exit",
        ),
        justify="center",
    )
    console.print()

    # Input directory: loop until it contains audio or the user gives up.
    while True:
        input_dir = browse_directory(
            "[bold]Select your audiobook directory[/bold]\n"
            "This should contain your FLAC+CUE or MP3 files"
        )
        if input_dir is None:
            return None

        flac_files = list(input_dir.rglob("*.flac"))
        mp3_files = list(input_dir.rglob("*.mp3"))
        if flac_files or mp3_files:
            break
        if not handle_no_audio_files(input_dir):
            return None

    if flac_files:
        display_files(flac_files, "Found FLAC Files")
    if mp3_files:
        display_files(mp3_files, "Found MP3 Files")

    output_dir = browse_directory(
        "[bold]Select output directory[/bold]",
        default=str(input_dir.parent / "out"),
    )
    if output_dir is None:
        return None

    # M4B creation method (convert always outputs M4B).
    method_choices = {
        "1": ("ffmpeg", "M4B using FFmpeg (recommended)"),
        "2": ("mp4box", "M4B using MP4Box"),
    }
    console.print("\n[bold]Choose M4B creation method:[/bold]")
    for key, (_, desc) in method_choices.items():
        console.print(f"{key}. {desc}")
    choice = Prompt.ask("Enter your choice", choices=list(method_choices), default="1")
    method = method_choices[choice][0]

    metadata = prompt_metadata()

    if not confirm_processing(flac_files or mp3_files, output_dir):
        return None

    return {
        "input_dir": input_dir,
        "output_dir": output_dir,
        "method": method,
        "bitrate": "64k",
        "dry_run": False,
        "resume": False,
        **metadata,
    }
