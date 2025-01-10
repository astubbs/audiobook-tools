#!/usr/bin/env python3
"""Verify script that runs tests, formatting checks, and linting."""

import argparse
import logging
import subprocess
import sys
from dataclasses import dataclass
from typing import List, Optional, Tuple

# Configure logging to only show warnings and above
logging.basicConfig(level=logging.WARNING)


@dataclass
class VerificationStep:
    """Represents a verification step with its command and description."""

    name: str
    command: List[str]
    check_command: Optional[List[str]] = None  # Alternative command for --check mode
    success_message: str = "passed"
    failure_message: str = "failed"


def run_command(step: VerificationStep, check_mode: bool = False) -> Tuple[bool, str]:
    """Run a verification step and return if it succeeded and its output.

    Args:
        step: The verification step to run
        check_mode: Whether to use check commands instead of fixing

    Returns:
        Tuple of (success, output)
    """
    print(f"\n=== {step.name} ===")
    
    # Use check command if in check mode and available
    command = step.check_command if check_mode and step.check_command else step.command
    
    result = subprocess.run(command, capture_output=True, text=True)
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
    parser = argparse.ArgumentParser(description="Run verification steps")
    parser.add_argument("--check", action="store_true", help="Check only, don't fix (for CI)")
    args = parser.parse_args()

    steps = [
        # Format code first
        VerificationStep(
            name="Running formatters",
            command=["black", "audiobook_tools"],
            check_command=["black", "--check", "audiobook_tools"],
        ),
        VerificationStep(
            name="Sorting imports",
            command=["isort", "audiobook_tools"],
            check_command=["isort", "--check-only", "audiobook_tools"],
        ),
        # Then run tests and checks
        VerificationStep(
            name="Running tests",
            command=["pytest", "--log-level=WARNING"],
        ),
        VerificationStep(
            name="Running linting",
            command=["pylint", "audiobook_tools"],
        ),
        VerificationStep(
            name="Running type checking",
            command=["mypy", "audiobook_tools"],
        ),
    ]

    failures: List[str] = []

    for step in steps:
        success, _ = run_command(step, check_mode=args.check)
        if not success:
            failures.append(step.name)
            if not args.check:
                # Only fail fast in local mode
                sys.exit(1)

    if failures:
        print("\n❌ Some verification steps failed:")
        for failure in failures:
            print(f"  - {failure}")
        sys.exit(1)


if __name__ == "__main__":
    main()
