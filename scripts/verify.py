#!/usr/bin/env python3
"""Verify script that runs tests, formatting checks, and linting."""

import subprocess
import sys
from typing import List, Tuple


def run_command(cmd: List[str], name: str) -> Tuple[bool, str]:
    """Run a command and return if it succeeded and its output."""
    print(f"\n=== {name} ===")
    result = subprocess.run(cmd, capture_output=True, text=True)
    output = result.stdout + result.stderr
    print(output)
    success = result.returncode == 0
    if success:
        print(f"✅ {name} passed")
    else:
        print(f"❌ {name} failed")
    return success, output


def main():
    """Run verification steps."""
    failures = []

    # Run tests
    success, _ = run_command(["pytest"], "Running tests")
    if not success:
        failures.append("Running tests")
        sys.exit(1)

    # Check code formatting
    success, _ = run_command(
        ["black", "--check", "."], "Checking code formatting (black)"
    )
    if not success:
        failures.append("Checking code formatting (black)")
        sys.exit(1)

    # Check import sorting
    success, _ = run_command(
        ["isort", "--check", "."], "Checking import sorting (isort)"
    )
    if not success:
        failures.append("Checking import sorting (isort)")
        sys.exit(1)

    # Run linting
    success, _ = run_command(["pylint", "audiobook_tools"], "Running linting (pylint)")
    if not success:
        failures.append("Running linting (pylint)")
        sys.exit(1)

    if failures:
        print("\n❌ Some verification steps failed:")
        for failure in failures:
            print(f"  - {failure}")
        sys.exit(1)


if __name__ == "__main__":
    main()
