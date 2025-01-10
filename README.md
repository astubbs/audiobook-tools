# Audiobook Tools

A Python package for processing audiobooks from CD rips (FLAC files with CUE sheets) into M4B audiobooks with proper chapter markers.

## Features

- Combines multiple FLAC files into a single audiobook
- Processes and combines CUE sheets for chapter markers
- Creates M4B audiobooks with chapters using FFmpeg or MP4Box
- Supports metadata (title, artist) and cover art
- Optimized settings for spoken word audio
- Dry run mode to preview changes

## Installation

### Prerequisites

Install system dependencies:

```bash
# macOS (using Homebrew)
brew install ffmpeg mp4box sox

# Ubuntu/Debian
sudo apt-get install ffmpeg gpac sox
```

### Install the Package

```bash
# Install in development mode
pip install -e .

# Install with development tools
pip install -e ".[dev]"
```

## Usage

### Basic Usage

Process an audiobook directory into an M4B file:

```bash
audiobook-tools process ./audiobook-directory
```

This will:
1. Find and merge all FLAC files
2. Process CUE sheets for chapters
3. Convert to AAC with optimal spoken word settings
4. Create an M4B file with chapters

### Advanced Usage

```bash
# Process with all options
audiobook-tools process ./input-dir \
    --output-dir ./out \
    --format m4b-ffmpeg \
    --bitrate 64k \
    --title "A New Earth" \
    --artist "Eckhart Tolle" \
    --cover cover.jpg

# Just combine CUE files
audiobook-tools combine-cue ./input-dir ./out

# Preview what would happen
audiobook-tools process ./input-dir --dry-run
```

### Options

- `--format, -f`: Output format (`m4b-ffmpeg`, `m4b-mp4box`, or `aac`)
- `--bitrate, -b`: Audio bitrate (default: 64k for spoken word)
- `--title, -t`: Audiobook title
- `--artist, -a`: Artist/author name
- `--cover, -c`: Cover art image file
- `--dry-run, -d`: Show what would be done without making changes
- `--debug`: Enable debug logging

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

## Development

### Setup Development Environment

```bash
# Install development dependencies
make install

# Run tests
make test

# Run linting
make lint

# Run type checking
make type

# Format code
make format

# Run all checks
make check
```

### Project Structure

```
audiobook_tools/
├── core/           # Core processing logic
│   ├── cue.py     # CUE sheet processing
│   └── processor.py # Main audiobook processor
├── cli/           # Command-line interface
│   └── main.py    # CLI implementation
└── utils/         # Utility functions
    └── audio.py   # Audio processing utilities
```

## Troubleshooting

### Common Issues

1. **No FLAC files found**: Ensure your FLAC files have "CD" in their names and are in the correct directory structure.
2. **Invalid CUE format**: Check that your CUE files are properly formatted and use UTF-8 encoding.
3. **FFmpeg errors**: Make sure you have FFmpeg installed with AAC support.

### Debug Mode

Run commands with `--debug` for detailed logging:

```bash
audiobook-tools --debug process ./input-dir
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Run tests and checks: `make check`
4. Submit a pull request

## License

MIT License - See LICENSE file for details 