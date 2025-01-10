#!/usr/bin/env python3
"""Script to run all verification steps locally."""

import subprocess
import sys
from typing import List, Tuple


def run_command(command: List[str]) -> Tuple[int, str, str]:
    """Run a command and return its exit code, stdout, and stderr."""
    try:
        result = subprocess.run(command, capture_output=True, text=True)
        return result.returncode, result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        return e.returncode, e.stdout, e.stderr


def main():
    """Run all verification steps."""
    steps = [
        (["poetry", "run", "pytest"], "Running tests"),
        (["poetry", "run", "black", "--check", "audiobook_tools"], "Checking code formatting (black)"),
        (["poetry", "run", "isort", "--check", "audiobook_tools"], "Checking import sorting (isort)"),
        (["poetry", "run", "pylint", "audiobook_tools"], "Running linting (pylint)"),
        (["poetry", "run", "mypy", "audiobook_tools"], "Running type checking (mypy)"),
    ]

    failed_steps = []

    for command, description in steps:
        print(f"\n=== {description} ===")
        exit_code, stdout, stderr = run_command(command)
        
        if stdout:
            print(stdout)
        if stderr:
            print(stderr, file=sys.stderr)
        
        if exit_code != 0:
            failed_steps.append(description)
            print(f"❌ {description} failed")
        else:
            print(f"✅ {description} passed")

    if failed_steps:
        print("\n❌ Some verification steps failed:")
        for step in failed_steps:
            print(f"  - {step}")
        sys.exit(1)
    else:
        print("\n✅ All verification steps passed!")
        sys.exit(0)


if __name__ == "__main__":
    main() 