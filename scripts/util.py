import os
import subprocess
import sys
from pathlib import Path

from west import log


def in_venv() -> bool:
    return sys.prefix != sys.base_prefix


def run_command(subcmd: str, cwd: str | None = None) -> str:
    """Run the command in given directory.

    Terminates if command failed; returns command stdout.
    """
    try:
        if cwd is None:
            cwd = str(Path.cwd())

        log.inf(f"Running `{subcmd}` in {cwd}", colorize=True)
        result: bytes = subprocess.check_output(subcmd, shell=True, cwd=cwd)  # noqa: S602
        return result.decode("utf-8").strip()
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        log.die(f"Cmd failed: {e}")
