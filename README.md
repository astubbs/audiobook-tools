# Audiobook Tools

Convert CD rips (FLAC+CUE) and MP3 files into M4B audiobooks with chapter markers.

## Features

- Merges multi-CD FLAC files or MP3 collections into a single audiobook
- Generates chapter markers from CUE sheets or MP3 filenames
- Creates M4B files with embedded chapters via FFmpeg or MP4Box
- Supports metadata: title, artist, cover art
- Resume support to skip already-completed steps
- Dry-run mode to preview without changes

## Requirements

- Python 3.10+
- ffmpeg / ffprobe
- sox (for FLAC merging)
- MP4Box (optional, alternative M4B method)

```bash
# macOS
brew install ffmpeg mp4box sox

# Ubuntu/Debian
sudo apt-get install ffmpeg gpac sox
```

## Installation

```bash
pip install -e .
```

Verify external tools are available:

```bash
audiobook check-tools
```

### Run without installing

To try it straight from a checkout without a global install, use the launcher script.
It builds a local virtualenv on first run and then executes the CLI:

```bash
bin/run                              # launch the interactive TUI
bin/run convert ./yourbook -o ./out  # run a subcommand
bin/run check-tools
```

Equivalently, once the virtualenv exists you can call it directly - `.venv/bin/audiobook`
- or run the package as a module: `python -m audiobook_tools`.

## Interactive mode

Run with no arguments to launch a guided terminal interface that walks you through
picking the input and output directories, the M4B method, and metadata, then runs the
conversion:

```bash
audiobook
```

Prefer a non-interactive run? Use `--no-tui` (or just pass a subcommand like
`convert` directly).

## Quick Start

Convert a FLAC+CUE audiobook in one command:

```bash
audiobook convert ./path/to/audiobook/
```

This will:
1. Find and merge all FLAC files (sorted by CD number)
2. Combine CUE sheets with adjusted timestamps
3. Encode to AAC (64k, optimized for spoken word)
4. Create M4B with chapter markers

Each step is labelled as it runs (with the underlying `sox`/`ffmpeg` progress shown
for the long ones), and a summary of the finished audiobook - path, duration, chapter
count, and elapsed time - prints at the end.

### Options

```bash
audiobook convert ./audiobook/ \
  --bitrate 96k \
  --title "Book Title" \
  --artist "Author Name" \
  --cover ./cover.jpg \
  --method mp4box \
  --output-dir ./output/ \
  --resume \
  --dry-run
```

## Input Formats

### FLAC + CUE (CD Rips)

```
Audiobook Name/
  CD1/
    audiofile.flac
    audiofile.cue
  CD2/
    audiofile.flac
    audiofile.cue
```

### MP3 Files

```
Audiobook Name/
  01 - Introduction.mp3
  02 - Chapter One.mp3
  03 - Chapter Two.mp3
```

Chapter titles are extracted from filenames.

## Individual Commands

Run pipeline steps independently:

```bash
# Merge audio files only
audiobook merge ./audiobook/ --dry-run

# Combine CUE sheets
audiobook combine-cue ./audiobook/ -o ./out/combined.cue

# Generate chapter file from CUE
audiobook chapters ./out/combined.cue --audio-file ./out/combined.flac

# Check tool availability
audiobook check-tools
```

## Output

All output goes to `./out/` by default:

```
out/
  combined.flac     # Merged audio
  combined.cue      # Combined CUE sheet
  chapters.txt      # Chapter metadata
  audiobook.aac     # Encoded audio
  audiobook.m4b     # Final audiobook
```

## Technical Details

### Chapter Formats

- **FFmpeg metadata** (default) - best compatibility with audio players
- **MP4Box** (alternative) - use `--method mp4box`

### CD Frame Format

CUE sheets use MM:SS:FF where FF is CD frames (75 per second). The tool handles all conversions between CD frames, milliseconds, and timestamp formats.

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run a specific test
pytest tests/test_time.py -v
```

## Project Structure

```
audiobook_tools/
  cli.py              # Click CLI entry point (group + subcommands)
  tui.py              # Interactive rich + questionary flow
  cue/
    parser.py          # CUE file parsing
    combiner.py        # Multi-CUE combination
  chapters/
    _common.py         # Shared CUE -> (start, title) helper
    ffmpeg.py          # FFmpeg metadata chapters
    mp4box.py          # MP4Box chapters
    mp3.py             # Chapters from MP3 filenames
  audio/
    merge.py           # Audio file merging + playback ordering
    encode.py          # AAC encoding
    m4b.py             # M4B creation
    probe.py           # ffprobe wrapper
  utils/
    time.py            # Time format conversions
    external.py        # External tool checking
tests/                # mocked unit tests (no real audio needed)
```

## License

MIT
