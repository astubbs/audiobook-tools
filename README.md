# Audio Book Chapter Tool

A tool to combine audio files and add chapter markers using CUE sheets.

## Overview

This toolset helps you convert CD rips (FLAC files with CUE sheets) into M4B audiobooks with proper chapter markers. The process involves:

1. Merging multiple FLAC files into a single file
2. Combining multiple CUE sheets into a single CUE file
3. Converting CUE chapters into chapter metadata
4. Creating the final M4B audiobook file

## Features

- Combines multiple audio files into a single M4B audiobook
- Adds chapter markers from CUE sheet
- Supports both MP4Box and FFmpeg methods for chapter embedding
- Can use existing AAC files to avoid re-encoding

## Requirements

- Python 3.x
- ffprobe (part of ffmpeg) for reading audio file durations
- FFmpeg for creating M4B audiobooks
- MP4Box (optional alternative method)
- sox (for merging FLAC files)

## Installation

1. Install the required Python packages:
```bash
pip install -r requirements.txt
```

2. Install system dependencies:
```bash
# macOS (using Homebrew)
brew install ffmpeg mp4box sox

# Ubuntu/Debian
sudo apt-get install ffmpeg gpac sox
```

## Usage

### Directory Structure

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

### Automated Processing

The easiest way to process your audiobook is to use the included script:

```bash
./process_audiobook.sh
```

This script will guide you through each step with confirmation prompts.

### Manual Steps

If you prefer to run the steps manually:

1. Merge FLAC files:
```bash
./merge_flac.sh
```

2. Generate combined CUE file:
```bash
python combine_cue.py
```

3. Generate chapter metadata and create M4B file using one of these methods:

#### Using FFmpeg (Recommended)

1. If you have an existing AAC file:
```bash
python cue-to-ffmpeg.py --input-aac "./out/your-audio.aac"
```

2. If you want to convert from FLAC:
```bash
python cue-to-ffmpeg.py
```

This will:
- Read the CUE file from `./out/combined.cue`
- Create a chapters file in FFmpeg metadata format
- Create an M4B audiobook with embedded chapters

#### Using MP4Box (Alternative)

```bash
python cue-to-mp4b.py
```

This will:
- Read the CUE file from `./out/combined.cue`
- Create a chapters file in MP4Box format
- Create an M4B audiobook with embedded chapters

### Updating Chapters Only

If you need to update just the chapter metadata without re-encoding the audio:

```bash
MP4Box -chap "./out/chapters.txt" "./out/audiobook.m4b"
```

## Technical Details

### Chapter Formats

MP4/M4B files support multiple chapter formats:
- QuickTime chapter format (used by iTunes/Apple)
- Nero chapter format
- FFmpeg metadata format
- MP4Box chapter format

This toolset supports two methods:
1. FFmpeg metadata format (recommended) - Better compatibility with audio players
2. MP4Box format (alternative) - Widely supported but may have issues with some players

### CD Frame Format

In CD audio:
- There are exactly 75 frames per second
- Time format is MM:SS:FF (minutes:seconds:frames)
- This tool handles the conversion from CD frames to milliseconds for accurate chapter markers

## Project Architecture

### Core Components

1. `merge_flac.sh` - Audio merger
   - Combines multiple FLAC files into one
   - Uses sox for lossless audio concatenation
   - Preserves audio quality

2. `combine_cue.py` - Main CUE combiner
   - Handles file discovery and processing
   - Manages CUE file combination logic
   - Core functions:
     - `time_to_seconds()`: Converts CUE time format (MM:SS:FF) to seconds
     - `seconds_to_time()`: Converts seconds back to CUE time format
     - `calculate_cumulative_duration()`: Calculates start times for each CD
     - `get_audio_length()`: Gets audio file duration using ffprobe

3. `cue-to-ffmpeg.py` - FFmpeg chapter converter
   - Converts combined CUE to FFmpeg metadata format
   - Handles time format conversion from CUE to milliseconds
   - Creates chapter markers for audiobook
   - Can use existing AAC files to avoid re-encoding

4. `cue-to-mp4b.py` - MP4Box chapter converter
   - Converts combined CUE to MP4Box chapter format
   - Alternative method for chapter embedding

5. `tests/test_combine_cue.py` - Test suite
   - Unit tests for time conversion functions
   - Integration tests for CD start time calculations
   - Mock tests for audio file duration handling

### Time Format Handling

The project handles multiple time formats:
- CUE format: `MM:SS:FF` (75 frames per second)
- FFmpeg format: Milliseconds with TIMEBASE=1/1000
- MP4B format: `HH:MM:SS.mmm` (millisecond precision)
- Internal calculations use milliseconds for accuracy

## Output Directory Structure

All output files are stored in the `./out` directory:

```
.
├── cue-to-ffmpeg.py  # FFmpeg-based chapter embedding
├── cue-to-mp4b.py    # MP4Box-based chapter embedding
└── out/
    ├── combined.flac     # Merged audio file
    ├── combined.cue      # Combined CUE sheet
    ├── chapters.txt      # Generated chapter metadata
    └── audiobook.m4b     # Final audiobook file
```

## Development

### Testing

Run the test suite to verify the time conversion functions:
```bash
python -m pytest tests/
```

Key test cases:
1. Time conversion accuracy
2. CD2 start time calculation
3. Frame rounding behavior
4. Edge cases (00:00:00, 00:00:74, etc.) 