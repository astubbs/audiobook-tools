# Audiobook Tools

A command-line tool for processing audiobooks with chapter markers. Convert FLAC+CUE audiobooks to M4B or AAC format with proper chapter markers and metadata.

## Features

- Merge multiple FLAC files into a single audiobook
- Process CUE sheets for chapter information
- Convert to M4B with chapters or AAC format
- Add metadata (title, artist, cover art)
- Beautiful terminal interface with progress tracking
- Support for both FFmpeg and MP4Box processing methods
- Optimized settings for spoken word audio (mono, 64k bitrate)
- Dry run mode to preview changes

## Quick Start

```bash
# Install dependencies
brew install ffmpeg gpac sox poetry  # macOS
sudo apt-get install ffmpeg gpac sox python3-poetry  # Ubuntu/Debian

# Clone and set up
git clone https://github.com/yourusername/audiobook-tools.git
cd audiobook-tools
poetry install

# Run the tool (choose one method):
poetry run audiobook-tools --help     # Run directly through Poetry
# OR
poetry env activate                   # Activate virtual environment
source $(poetry env info --path)/bin/activate.fish  # For fish shell
audiobook-tools --help               # Run command directly
```

## Installation

### Prerequisites

Install system dependencies:

```bash
# macOS (using Homebrew)
brew install ffmpeg gpac sox poetry

# Ubuntu/Debian
sudo apt-get install ffmpeg gpac sox python3-poetry
```

### Using Poetry (recommended)
```bash
# Clone and install
git clone https://github.com/yourusername/audiobook-tools.git
cd audiobook-tools
poetry install

# Run the tool
poetry run audiobook-tools --help
```

### System Requirements
- Python 3.8 or later
- FFmpeg (for audio processing)
- sox (for FLAC merging)
- MP4Box (optional, for alternative M4B creation)

## Directory Structure

Place your audiobook files in a directory structure like:

```
./Audiobook Name/
  ├── CD1/
  │   ├── audiofile.flac
  │   └── audiofile.cue
  ├── CD2/
  │   ├── audiofile.flac
  │   └── audiofile.cue
  └── ...
```

## Usage

### Basic Usage
```bash
# Process an audiobook directory (interactive mode with TUI)
audiobook-tools process ./audiobook-dir

# Just combine CUE sheets
audiobook-tools combine-cue ./audiobook-dir ./output-dir

# Preview what would happen
audiobook-tools process ./audiobook-dir --dry-run
```

### Advanced Usage
```bash
# Full options example
audiobook-tools process ./audiobook-dir \
    --output-dir ./out \
    --output-format m4b-ffmpeg \
    --bitrate 64k \
    --title "Book Title" \
    --artist "Author Name" \
    --cover cover.jpg
```

### Interface Options
- `--tui/--no-tui`: Enable/disable Terminal User Interface (default: enabled)
- `--interactive/--no-interactive`: Enable/disable interactive prompts (default: enabled)
- `--debug`: Enable debug logging
- `--dry-run`: Show what would be done without making changes

### Output Formats
- `m4b-ffmpeg`: M4B file with chapters using FFmpeg (recommended)
- `m4b-mp4box`: M4B file with chapters using MP4Box
- `aac`: AAC audio file without chapters

## Troubleshooting

### Common Issues

1. **No FLAC files found**: Ensure your FLAC files have "CD" in their names and are in the correct directory structure.
2. **Invalid CUE format**: Check that your CUE files are properly formatted and use UTF-8 encoding.
3. **FFmpeg errors**: Make sure you have FFmpeg installed with AAC support.

### Debug Mode

Run commands with `--debug` for detailed logging:

```bash
audiobook-tools --debug process ./audiobook-dir
```

## Development

```bash
# Install development dependencies
poetry install

# Run tests
poetry run pytest

# Run linting
poetry run black audiobook_tools tests
poetry run isort audiobook_tools tests
poetry run pylint audiobook_tools tests

# Run all checks
poetry run tox
```

For more detailed development guidelines, see [CONTRIBUTING.md](CONTRIBUTING.md).

## License

This project is licensed under the MIT License - see the LICENSE file for details. 