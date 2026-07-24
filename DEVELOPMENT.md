# Development Guide

## Setup

Requires Python 3.10+ and the external tools (`ffmpeg`, `ffprobe`, `sox`; `MP4Box`
optional). Install the package with dev dependencies:

```bash
pip install -e ".[dev]"
```

Verify the external tools are available:

```bash
audiobook check-tools
```

## Checks

```bash
pytest                 # run the test suite
ruff check .           # lint
ruff format .          # auto-format (CI uses --check)
```

CI (`.github/workflows/ci.yml`) runs the ruff lint + format gate and the pytest
matrix on Python 3.10-3.13, plus a dependency-review job on PRs.

## Project structure

```
audiobook_tools/
  cli.py              # click CLI: group + convert / merge / combine-cue / chapters / check-tools
  tui.py              # interactive rich + questionary flow (launched when no subcommand)
  audio/              # merge, encode, m4b, probe  (ffmpeg / sox / MP4Box wrappers)
  chapters/           # ffmpeg / mp4box / mp3 chapter generation (+ _common CUE helper)
  cue/                # CUE sheet parsing and combining
  utils/              # time-format conversions, external-tool checks
tests/                # mocked unit tests (no real audio needed)
```

## The pipeline

`convert` runs a linear pipeline: merge audio -> generate chapters -> encode to AAC
-> mux into M4B. Intermediate files land in the output directory; `--resume` reuses
any that already exist. The interactive TUI collects options and then invokes the
same `convert` command, so there is a single code path for the actual work.

## Conventions

- Type hints throughout; use `X | None` unions (Python 3.10+).
- Public functions and classes get docstrings.
- Mock external tools (`ffmpeg`, `sox`, `MP4Box`, `ffprobe`) in tests - never require
  real audio files.
- Use neutral, non-copyrighted sample data in tests, fixtures, and docs.
- Keep changes as simple as the code they replace; if you find complex code, simplify
  it in a separate change.

## Release process

1. Update the version in `pyproject.toml`.
2. Move `CHANGELOG.md`'s `[Unreleased]` entries under a new version heading.
3. Commit, tag (`vX.Y.Z`), push, and create a GitHub release. See `docs/LAUNCH.md`
   for the full first-release checklist.
