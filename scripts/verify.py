#!/usr/bin/env python3
"""Verify script that runs tests, formatting checks, and linting."""

import subprocess
import sys
from dataclasses import dataclass
from typing import List, Optional, Tuple


@dataclass
class VerificationStep:
    """Represents a verification step with its command and description."""

    name: str
    command: List[str]
    success_message: str = "passed"
    failure_message: str = "failed"


def run_command(step: VerificationStep) -> Tuple[bool, str]:
    """Run a verification step and return if it succeeded and its output.

    Args:
        step: The verification step to run

    Returns:
        Tuple of (success, output)
    """
    print(f"\n=== {step.name} ===")
    result = subprocess.run(step.command, capture_output=True, text=True)
    output = result.stdout + result.stderr
    print(output)

    success = result.returncode == 0
    if success:
        print(f"✅ {step.name} {step.success_message}")
    else:
        print(f"❌ {step.name} {step.failure_message}")
    return success, output


def main():
    """Run verification steps."""
    steps = [
        VerificationStep(
            name="Running tests",
            command=["pytest"],
        ),
        VerificationStep(
            name="Checking code formatting (black)",
            command=["black", "--check", "."],
        ),
        VerificationStep(
            name="Checking import sorting (isort)",
            command=["isort", "--check", "."],
        ),
        VerificationStep(
            name="Running linting (pylint)",
            command=["pylint", "audiobook_tools"],
        ),
        VerificationStep(
            name="Running type checking (mypy)",
            command=["mypy", "audiobook_tools"],
        ),
    ]

    failures: List[str] = []

    for step in steps:
        success, _ = run_command(step)
        if not success:
            failures.append(step.name)
            sys.exit(1)

    if failures:
        print("\n❌ Some verification steps failed:")
        for failure in failures:
            print(f"  - {failure}")
        sys.exit(1)


if __name__ == "__main__":
    main()
