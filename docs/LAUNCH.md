# Launch plan

A checklist and playbook for getting audiobook-tools "out there". This is a plan -
nothing here is executed automatically. Work top to bottom.

## 1. Pre-launch checklist (mechanical)

- [ ] Merge `develop` -> `main` (open a PR, let CI pass, squash or merge).
- [ ] Replace the `yourusername` placeholder in `README.md` with the real repo URL
      (`github.com/astubbs/audiobook-tools`).
- [ ] Add badges to the top of `README.md`: CI status, PyPI version, supported Python
      versions, license.
- [ ] Confirm `pyproject.toml` metadata is release-ready: `description`, `readme`,
      `license`, `requires-python`, `classifiers`, `project.urls` (Homepage, Source,
      Issues). Add `classifiers` if missing.
- [ ] Tag `v0.1.0` and write a GitHub Release from the `CHANGELOG.md` `[Unreleased]`
      section (move those entries under a `## [0.1.0]` heading first).
- [ ] Smoke-test a real conversion end to end on a sample book (FLAC+CUE and MP3).
- [ ] `audiobook check-tools` documents the external deps clearly for new users.

## 2. Distribution

**PyPI (primary).** The package is a standard setuptools/pyproject build.

- Build: `python -m build` (produces sdist + wheel in `dist/`).
- Publish via **Trusted Publishing** (OIDC) from a GitHub Actions release workflow -
  no long-lived API token to manage. Add a `release.yml` that runs on tag push and
  uses `pypa/gh-action-pypi-publish`. This is the preferred path.
- Fallback: `twine upload dist/*` with a PyPI API token stored as a repo secret.

**Install instructions** to advertise once published:

```bash
pipx install audiobook-tools      # isolated, recommended for a CLI
uv tool install audiobook-tools   # if the user has uv
pip install audiobook-tools       # into an existing environment
```

Remind users that `ffmpeg`, `ffprobe`, and `sox` are external (brew/apt), and
`MP4Box` is optional.

**Later:** a Homebrew formula/tap for a one-line `brew install` once there is demand.

## 3. Demo asset

A short recording carries the interactive TUI far better than prose. Use the
`ce-demo-reel` skill (or `asciinema` + `agg`, or a GIF) to capture:

- Launching `audiobook` with no args and walking the guided flow.
- The per-step progress and the final completion summary.

Embed the GIF/asciinema near the top of the README, and reuse it in launch posts.

## 4. Announcement channels

Lead with the problem it solves (turn a pile of CD rips / loose MP3s into a proper
chaptered M4B for Apple Books / Plexamp), not the tech. Tailor the angle per venue:

- **Show HN** - "Show HN: audiobook-tools - turn CD rips and MP3s into chaptered M4B".
  Emphasize the interactive TUI, chapter handling, and that it wraps ffmpeg/sox so you
  don't have to.
- **r/audiobooks, r/audiobookshelf** - end-user framing: get your ripped/loose files
  into a single chaptered file your player understands.
- **r/DataHoarder, r/selfhosted** - archival/library framing; pairs with
  Audiobookshelf/Plex libraries.
- **r/Python** - the packaging/CLI+TUI angle (click + rich + questionary, tested,
  CI'd).
- **r/audiophile, r/plexamp** - spoken-word-optimized encoding, chapter markers.
- **MobileRead forums** - an active, long-lived audiobook/e-reader community that
  appreciates conversion tooling.
- **A short blog post / dev.to / personal site** - the canonical write-up the posts
  link back to.

**Reusable one-paragraph pitch:**

> audiobook-tools turns CD rips (FLAC+CUE) and loose MP3 collections into a single
> chaptered M4B audiobook - merging the files, building chapter markers, and encoding
> for spoken word - from one command or a guided terminal UI. It wraps ffmpeg, sox,
> and (optionally) MP4Box so you don't have to hand-write the pipeline.

## 5. Positioning

- **Value prop:** "From CD rips and loose MP3s to a clean, chaptered M4B - in one
  command or a guided TUI."
- **Target user:** people who rip audiobook CDs or collect MP3 audiobooks and want a
  single chaptered file for Apple Books, Plexamp, Audiobookshelf, or their car.
- **Why not just X:**
  - *Manual ffmpeg* - works, but you hand-build concat lists, chapter metadata, and
    encoding flags every time; this automates that and handles CUE math.
  - *m4b-tool* - powerful but PHP and heavier to set up; this is a pip-installable
    Python CLI with an interactive mode.
  - *Audiobookshelf / Plex* - libraries/servers for *playing* audiobooks, not for
    *building* a chaptered M4B from raw rips. Use this to produce the file, then add
    it to those.
