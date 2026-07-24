# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Interactive terminal UI (`rich` + `questionary`): running `audiobook` with no
  subcommand launches a guided flow (pick input/output directories, method, and
  metadata), then runs the conversion. Disable with `--no-tui`.
- Per-step progress output and a completion summary (output path, duration, chapter
  count, elapsed time) for `convert`. Long steps show the underlying tool's own
  progress (sox/ffmpeg).
- End-to-end integration tests that run the real ffmpeg/MP4Box pipeline against small,
  non-copyrighted spoken-word sample files, so the actual production flow is verified
  (not just mocked). CI now installs ffmpeg/sox/MP4Box so these run in CI too.

### Changed
- MP3 chapter generation moved into a dedicated, tested module
  (`chapters/mp3.py`) with more robust filename title extraction and duplicate-title
  disambiguation.
- MP3 files are now gathered in a single, consistent playback order for both merging
  and chapter generation, so chapter timestamps always align with the audio.
- CUE chapter parsing is now shared between the FFmpeg and MP4Box generators via the
  structured CUE parser, fixing a case where an album-level `TITLE` could leak into
  the chapter list.

### Fixed
- MP3 conversion no longer fails when the input directory is relative and the output
  directory differs: the ffmpeg concat list now uses absolute paths (the concat demuxer
  resolves relative entries against the list file's location, not the CWD).
- MP3 conversion with `--method mp4box` now writes a valid MP4Box chapter file;
  previously it emitted the ffmpeg metadata format, which MP4Box could not import.
- Media tools are now invoked with stdin disconnected, avoiding intermittent failures
  when run as a subprocess.
- `.gitignore` no longer hardcodes specific book titles; audio artifacts are ignored
  generically.
