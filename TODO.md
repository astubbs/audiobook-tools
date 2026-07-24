# TODO

## Fold in the audiobook *generator*

There is a sibling project, referred to only as **`audiobook-generator`**, that does
the one thing `audiobook-tools` does not: **generate** audiobook audio from source text.

- `audiobook-generator`: PDF -> extract text / parse TOC -> TTS -> chaptered audio
  (currently an early skeleton; the TTS/audio half is unimplemented stubs).
- `audiobook-tools` (this repo): existing audio (FLAC+CUE, MP3) -> **package** into
  M4B/AAC with chapter markers + metadata.

They are the *generate* and *package* halves of one audiobook pipeline. The plan is to
consolidate them here so this repo is the single audiobook toolchain, exposed as an
`audiobook generate` command that feeds the existing packaging pipeline.

See [docs/FOLD_IN_GENERATOR.md](docs/FOLD_IN_GENERATOR.md) for the full plan: the UI
assessment (standardize on this repo's click + rich + questionary stack), approach
pros/cons, a phased shape, and the copyright-scrub checklist.
