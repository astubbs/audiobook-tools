# Contributing Guide

Thanks for helping improve audiobook-tools. This project converts existing audio
(CD rips as FLAC+CUE, or MP3 collections) into chaptered M4B audiobooks, with both a
scriptable CLI and an interactive TUI.

See [DEVELOPMENT.md](DEVELOPMENT.md) for setup, the check commands, and the project
structure.

## Before opening a PR

- `ruff check .` and `ruff format --check .` pass.
- `pytest` passes; new behavior has tests.
- User-facing changes update the README and add a `CHANGELOG.md` `[Unreleased]` entry.

## Commit messages

Use conventional-commit prefixes: `feat:`, `fix:`, `refactor:`, `docs:`, `test:`,
`chore:`. Keep the subject under ~50 chars; explain the "why" in the body when it is
not obvious.

## Code style

- PEP 8 via `ruff` (line length 100); run `ruff format`.
- Type hints throughout (`X | None` unions, Python 3.10+).
- Docstrings on public functions and classes.
- Descriptive names; keep functions focused. If you disable a lint rule, comment why.

## Testing

- Tests verify behavior and outcomes. It is fine to assert on constructed subprocess
  commands where the command *is* the behavior (e.g. the ffmpeg/sox/MP4Box argv), but
  don't over-couple to incidental implementation details.
- Mock external tools (`ffmpeg`, `ffprobe`, `sox`, `MP4Box`) - tests must not require
  real audio.
- Cover edge cases: empty input, missing files, malformed names.
- Use neutral, invented sample data. **Never reference real copyrighted works or
  authors** in tests, fixtures, or docs.

## Notes for AI assistants

- Read the full file before editing; preserve existing error handling, logging, and
  docstrings.
- Keep the TUI optional but enabled by default; maintain both TUI and CLI paths.
- Handle paths cross-platform (`pathlib`); check for `None`/empty values.
- Don't assume every optional dependency is installed (`MP4Box` is optional).
- Keep changes as simple as the code they replace.
