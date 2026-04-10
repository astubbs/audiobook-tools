"""Utilities for checking external tool availability."""

import shutil


def check_tool(name: str) -> bool:
    """Check if an external tool is available on PATH."""
    return shutil.which(name) is not None


def require_tool(name: str) -> None:
    """Raise SystemExit if an external tool is not available."""
    if not check_tool(name):
        raise SystemExit(
            f"Error: '{name}' is not installed or not on PATH.\n"
            f"Install it and try again. See README.md for installation instructions."
        )
