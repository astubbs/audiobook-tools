# Folding in `audiobook-generator`

## Why

There is a sibling project, referred to here only as **`audiobook-generator`**, that is
the *generate* half of one audiobook pipeline: source text (PDF) -> extract text and
parse a table of contents -> text-to-speech -> chaptered audio. `audiobook-tools` (this
repo) is the *package* half: existing audio -> chaptered M4B/AAC with metadata.

The goal is to consolidate them so this repo is a single audiobook toolchain:
**generate audio from text, then package it into an audiobook**, ideally exposed as an
`audiobook generate` command that hands its output to the existing packaging pipeline.

This document is the plan for that fold-in. **No generator code has been ported yet.**

> **Naming/copyright rule:** refer to the sibling only as `audiobook-generator`. Never
> put its former repo name, or any author/work referenced in its sample data, into this
> repository (code, docs, commits, or history). This repo is public.

## Current state of `audiobook-generator` (researched)

It is an **early skeleton** (package `pdf_book_tts`). Important implications:

- The **TTS, audio-combine, and M4A steps are stubs** that only log "Would
  convert..." and return success. There is **no `torch`/Coqui or any TTS engine
  installed** - the audio-generation half does not exist yet.
- Substantive, reusable parts today: **PDF text extraction / cleaning / chunking**
  (`pdf/`, `text/`, built on `pdfplumber`) and a **stage/resume workflow abstraction**
  (`workflow/stage.py` + `StageManager` + `processor.py`).
- The workflow abstraction is richer than our linear pipeline (enum stages, per-stage
  confirmation, filesystem checkpointing) but is **partial and buggy**: resume gating
  only takes effect when *both* `--stage` and `--resume` are given, and there is a
  field-name mismatch (`no_confirm` vs `auto_confirm`). Both need fixing before reuse.

## UI toolkit: nothing to adopt

This is sometimes framed as "which TUI framework wins" - but it is not a contest,
because `audiobook-generator` has **no TUI framework at all**:

| Layer | audiobook-generator | audiobook-tools |
|---|---|---|
| CLI | stdlib `argparse`, one flat command | `click` groups + subcommands |
| Interactive | one raw `input()` Y/n gate | `questionary` menus / path pickers |
| Progress | stdlib `logging` lines only | styled step output + tool-native progress |
| Styling | none | `rich` panels / tables / colors |

**Decision: standardize on this repo's `click` + `rich` + `questionary` stack.** The
only UI work in the fold-in is a **mechanical port** - replace the generator's
`argparse` parser with a `click` command and its `logging` progress lines with our
styled output. Migration is strictly one-directional; nothing flows back.

## Fold-in approaches - pros / cons

Recommended path marked **[rec]**.

### Integration shape
- **[rec] Single unified package.** Add an `audiobook generate` command to this repo's
  click CLI; the generator's `pdf/` + `text/` + workflow become subpackages. Heavy,
  future TTS dependencies go behind an optional extra
  (`pip install "audiobook-tools[generate]"`) so the core packaging tool stays a
  single-`click` dependency.
  *Pro:* one install, one CLI, shared packaging code. *Con:* one repo to keep coherent.
- Separate co-located package in this repo. *Pro:* isolation. *Con:* extra packaging
  overhead, split CLI.
- Keep two repos, cross-link only. *Pro:* least effort now. *Con:* defeats the
  "one toolchain" goal.

### Workflow engine
- **[rec, skateboard] Keep the linear pipeline.** Give `generate` its own simple linear
  flow, reusing the `--resume` (skip-if-exists) approach `convert` already uses.
  *Pro:* small, predictable, no new abstraction. *Con:* less granular checkpointing.
- Adopt + fix the generator's `StageManager` as a shared engine for both `convert` and
  `generate`. *Pro:* per-stage confirmation, typed checkpoint cache. *Con:* must fix the
  two bugs and re-home `convert` onto it - larger blast radius. Revisit once `generate`
  actually has several heavy stages worth checkpointing.

### Git history
- **[rec] Fresh copy, no history.** Copy the current clean generator tree in as new
  files; never merge its git history. *Pro:* the public repo never inherits any tainted
  history. *Con:* loses upstream commit provenance (acceptable).
- `git subtree` / `filter-repo` merge after scrubbing. *Pro:* preserves history.
  *Con:* risks dragging tainted objects into a public repo; more fragile.

### Dependencies
- PDF side is light (`pdfplumber`). The future TTS side is heavy (`torch` + a TTS
  engine) - keep it **strictly optional** via the `[generate]` extra so installing the
  packaging tool never pulls in gigabytes of ML dependencies.

## Recommended shape (phased)

- **Phase 1 - the seam + PDF port.** Add `audiobook generate`; port PDF
  extraction/cleaning/chunking; migrate `argparse` -> `click` and `logging` -> our
  styled progress; wire the generated audio output into the existing `chapters/` +
  `audio/m4b.py` packaging. Keep TTS as an optional stub behind `[generate]`.
- **Phase 2 - real TTS.** Integrate an actual TTS engine (net-new work, since upstream
  never implemented it) behind the optional extra, with progress shown through our
  styled output.

## Deliverable: a matched PDF + audio golden test dataset

When the generator is folded in, build a **round-trip integration test** analogous to the
packaging pipeline's `tests/test_integration.py` (which uses non-copyrighted `say`-
generated MP3s). The generate side needs a matched pair:

1. Write short, **original** chapter text (no third-party works).
2. Render it to a small PDF fixture (the generator already depends on `reportlab`, which
   builds PDFs, so reuse that to generate the fixture deterministically).
3. Run the `generate` pipeline: PDF -> extracted text -> TTS -> chaptered audio.
4. Assert the extracted text matches the source, and that chapter count/titles/order in
   the produced audio match expectations.

Because TTS output is not byte-reproducible across engines/versions, compare on
**structure** (chapter boundaries, titles, approximate durations), not exact audio bytes -
the same tolerance approach the packaging integration test uses. If a golden audio
artifact is wanted, commit one generated once and compare structurally, iterating the text
until the pair is stable. Keep the PDF and any audio fixtures small and clearly original.

## Copyright-scrub checklist (applies whichever approach)

- Exclude the generator's `samples/` and `output/` directories entirely.
- `grep -ri` the ported tree for the old name and any author/work from its sample data;
  remove all matches.
- Rename any identifying test fixtures to neutral, invented names.
- Verify nothing copyrighted enters this repo's git history (prefer the fresh-copy
  approach above).
