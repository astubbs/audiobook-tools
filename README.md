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

# Run the tool
poetry run audiobook-tools
```

The tool will launch with an interactive Terminal User Interface (TUI) that will guide you through the process step by step.

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

# If using fish shell, you must activate the virtualenv first:
poetry env activate  # This will show the source command
source /path/to/virtualenv/bin/activate.fish

# Run the tool
audiobook-tools
```

> **Note for fish shell users**: Due to [known issues with Poetry and fish shell](https://github.com/python-poetry/poetry-plugin-shell/issues/7), 
> you need to activate the virtualenv manually using `source` instead of using `poetry run`. This ensures the correct Python environment 
> is used and avoids path management issues that can occur when Poetry tries to manage shell execution directly.

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
Simply run the tool and follow the interactive prompts:
```bash
audiobook-tools
```

The Terminal User Interface (TUI) will guide you through:
1. Selecting your audiobook directory
2. Choosing an output directory
3. Selecting output format
4. Adding metadata (title, artist, cover art)
5. Processing the audiobook

### Command Line Options
For automation or advanced usage, you can explore the available options:

```bash
# Show all available commands
audiobook-tools --help

# Show options for a specific command
audiobook-tools process --help
audiobook-tools combine-cue --help
```

Example usage without TUI:

```bash
# Process without TUI
audiobook-tools process ./audiobook-dir \
    --no-tui \
    --output-dir ./out \
    --output-format m4b-ffmpeg \
    --bitrate 64k \
    --title "Book Title" \
    --artist "Author Name" \
    --cover cover.jpg

# Preview what would happen
audiobook-tools process ./audiobook-dir --dry-run

# Just combine CUE sheets
audiobook-tools combine-cue ./audiobook-dir ./output-dir
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

## Contributing

For development setup and guidelines, see [DEVELOPMENT.md](DEVELOPMENT.md).

## License

This project is licensed under the MIT License - see the LICENSE file for details. 