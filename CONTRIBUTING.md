# Contributing Guide

## Project Context

This project helps process audiobooks from CD rips (typically FLAC files with CUE sheets) into M4B audiobooks. It's designed to:
- Handle multi-CD audiobooks
- Preserve chapter information
- Optimize for spoken word audio
- Provide both CLI and TUI interfaces
- Support different processing methods (FFmpeg/MP4Box)

## For Language Models

This section provides context and guidelines specifically for LLMs assisting with this project:

### Project Philosophy
- Favor user experience and robustness over minor optimizations
- Provide clear feedback and progress indication for long-running operations
- Support both modern (TUI) and traditional (CLI) interfaces
- Maintain backward compatibility when possible

### Test Design Guidelines
- Tests should verify behavior and outcomes, not implementation details
- Avoid over-specifying exact commands, call orders, or implementation specifics
- Focus on what the code does, not how it does it
- Allow for flexibility in the implementation while ensuring correct behavior
- Mock external dependencies but don't be too strict about exact command parameters
- Use reasonable sample data that demonstrates the feature without referencing real copyrighted works

### Common LLM Considerations
- Always read existing file content before suggesting edits
- Maintain consistent code style with the existing codebase
- Preserve useful comments and docstrings when modifying code
- Don't remove error handling or logging
- Keep the TUI optional but enabled by default
- Remember that users might not have all dependencies installed
- Always use git commands for file operations (`git mv` for moves/renames, `git rm` for deletions)

### Known LLM Pitfalls
- Suggesting incomplete imports
- Removing error handling in favor of shorter code
- Forgetting to handle file paths cross-platform
- Not checking for None or empty values
- Generating code without proper type hints
- Removing useful debug logging
- Making assumptions about installed dependencies

### When Making Changes
- Read the full context before suggesting changes
- Explain why changes are being made
- Keep existing error handling and logging
- Maintain both TUI and CLI functionality
- Test edge cases (empty input, missing files, etc.)
- Consider cross-platform compatibility
- Preserve existing comments and documentation
- Keep changes as simple as the code that was replaced: don't make things more complicated

### Documentation Guidelines
- Keep explanations in code comments
- Update README for user-facing changes
- Update this guide for architectural changes
- Add type hints and docstrings
- Document any new dependencies

## Development Guidelines

### Git Commits

- Use semantic commit messages:
  - `feat:` for new features
  - `fix:` for bug fixes
  - `refactor:` for code changes that neither fix bugs nor add features
  - `docs:` for documentation changes
  - `test:` for test changes
  - `chore:` for maintenance tasks

- Format:
  ```
  type: concise subject line (50 chars or less)

  More detailed explanatory text. Wrap at 72 characters. The blank
  line separating the summary from the body is critical.

  - Bullet points are okay
  - Use a hyphen followed by a space
  - List any breaking changes or issues closed
  ```

### Code Style

- Use Black for code formatting (88 character line length)
- Follow isort for import sorting
- Follow pylint guidelines with our custom rules
- Add docstrings to all public functions and classes
- Use type hints consistently
- Keep functions focused and small
- Use clear, descriptive variable names
- If disabling lint rules, comment the justification

### Testing

- Write tests for new features
- Update tests when modifying existing features
- Use pytest fixtures for common test setups
- Test both success and failure cases
- Mock external dependencies (FFmpeg, sox, etc.)

### Documentation

- Keep README focused on getting users started
- Document complex functions and modules
- Include examples for non-obvious features
- Update docs when changing functionality
- Add comments for complex algorithms

### Project Structure

```
audiobook_tools/
├── core/           # Core processing logic
│   ├── cue.py     # CUE sheet processing
│   └── processor.py # Main audiobook processor
├── cli/           # Command-line interface
│   ├── main.py    # CLI implementation
│   └── tui.py     # Terminal UI components
└── utils/         # Utility functions
    └── audio.py   # Audio processing utilities
```

### Expected Directory Structure

For audiobooks, we expect:
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

## Release Process

1. Update version in pyproject.toml
2. Update CHANGELOG.md
3. Create a release commit
4. Tag the release
5. Push to main branch
6. Create GitHub release

## Common Issues & Solutions

Document common issues and their solutions here to help future contributors:

1. **FFmpeg Errors**: Usually related to codec support or version mismatches
2. **CUE Sheet Issues**: Often encoding-related or format problems
3. **Performance**: Large file operations need progress feedback
4. **Cross-platform**: Path handling needs special attention 