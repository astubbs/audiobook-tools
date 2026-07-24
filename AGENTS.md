# AGENTS.md - rules for contributors and AI agents

These rules apply to everyone working in this repo - human contributors and AI coding
agents alike (Claude Code, the `@claude` and code-review GitHub bots, Cursor, Copilot,
etc.). Claude Code also reads `CLAUDE.md` if present; this file is the shared, canonical
source so the rules travel with the repo rather than living in one person's config.

## What this project is

`audiobook-tools` packages existing audio (CD rips as FLAC+CUE, or MP3 collections) into
chaptered M4B audiobooks. It wraps `ffmpeg`, `ffprobe`, `sox`, and optionally `MP4Box`.
See `DEVELOPMENT.md` for setup and architecture, `CONTRIBUTING.md` for the PR checklist.

## Copyright hygiene (non-negotiable, this is a public repo)

- Never commit copyrighted material, and never reference a real copyrighted work or
  author in code, tests, fixtures, docs, commit messages, or git history.
- Test/sample data must be **original and non-copyrighted**. The audio fixtures under
  `tests/data/` were generated from original text; keep any new fixtures the same way.
- A sibling project is referred to **only** as `audiobook-generator`. Do not introduce
  its former name or any author/work from its sample data into this repo (see
  `docs/FOLD_IN_GENERATOR.md`, including the copyright-scrub checklist, before folding it
  in).

## Toolchain and commands

- Python 3.10+, setuptools + `pyproject.toml`, `click` + `rich` + `questionary`.
- Install: `pip install -e ".[dev]"`. Run without installing: `bin/run` (auto-builds a
  venv) or `python -m audiobook_tools`.
- Before every change is done: `ruff check .`, `ruff format .`, and `pytest` must pass.
  Run the **full** suite, not just changed files.

## Code quality

- Be DRY: reuse and refactor shared patterns into shared modules; do not copy-paste or
  write parallel implementations that drift.
- Validate user input; handle errors visibly (never swallow exceptions).
- Give things meaningful, descriptive names.
- Type hints throughout (`X | None` unions); docstrings on public functions and classes.
- Do not use em-dash or double-dash characters; use a single dash (-).

## Testing

- New code comes with tests, in the same change - not "later".
- Mock external tools (`ffmpeg`, `ffprobe`, `sox`, `MP4Box`) in unit tests; they must not
  require real audio. End-to-end tests that do run the real tools live in
  `tests/test_integration.py` and skip when the tools are absent.
- User-facing changes update the README and add a `CHANGELOG.md` `[Unreleased]` entry.

## Branches

- `develop` is the integration branch; `main` is the release branch. Open PRs against
  `main` from a descriptively named branch. After opening a PR, address any
  duplicate-code / similarity reports for duplication introduced by that PR.
