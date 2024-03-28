"""
Scripts to be run with 'poetry run' command.
Poetry cannot run shell scripts in its scripts section, so we have to use Python scripts instead.
"""

import subprocess


def format_code() -> None:
    """
    Format the code using black
    """
    subprocess.run(["black", "app/"], check=False)


def format_code_check() -> None:
    """
    Check if the code is formatted correctly using black
    """
    subprocess.run(["black", "--check", "app/"], check=False)


def lint_code() -> None:
    """
    Lint the code using pylint
    """
    subprocess.run(["pylint", "app/"], check=False)


def type_check() -> None:
    """
    Type check the code using mypy
    """
    subprocess.run(["mypy", "app/"], check=False)


def security_check() -> None:
    """
    Check for security vulnerabilities using bandit
    """
    subprocess.run(["bandit", "-r", "app"], check=False)


def run_tests() -> None:
    """
    Run the tests using pytest
    """
    subprocess.run(["pytest"], check=False)
