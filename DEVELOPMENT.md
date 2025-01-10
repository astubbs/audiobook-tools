# Development Guide

## Setup

1. Install Python 3.8 or higher
2. Install Poetry for dependency management
3. Install development dependencies:
   ```bash
   poetry install
   ```

## Verification

Run all checks with:
```bash
python scripts/verify.py
```

This runs:
- Tests (pytest)
- Code formatting (black)
- Import sorting (isort)
- Linting (pylint)
- Type checking (mypy)

You can also run individual checks:
```bash
# Run tests
poetry run pytest

# Run linting
poetry run black audiobook_tools tests
poetry run isort audiobook_tools tests
poetry run pylint audiobook_tools tests

# Run type checking
poetry run mypy audiobook_tools
```

## Contributing Guidelines

1. **Code Style**
   - Follow PEP 8
   - Use type hints
   - Format code with black
   - Sort imports with isort

2. **Code Changes**
   - Keep changes as simple as the code that was replaced
   - Don't make things more complicated than they need to be
   - If you find complex code, simplify it in a separate PR

3. **Linting**
   - If disabling lint rules, comment the justification
   - Example:
     ```python
     # pylint: disable=too-many-locals
     # This function processes CUE sheets which require tracking multiple local variables
     # Breaking it up would make the code harder to understand
     def parse_cue_file(...):
     ```

4. **Testing**
   - Write tests for new features
   - Maintain test coverage
   - Use pytest fixtures for test setup

5. **Documentation**
   - Update docstrings for changed code
   - Keep README.md focused on user documentation
   - Add development notes here in DEVELOPMENT.md 