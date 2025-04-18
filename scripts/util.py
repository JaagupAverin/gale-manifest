import os
import subprocess
import sys
from dataclasses import dataclass

from dotenv import load_dotenv
from west import log


def in_venv() -> bool:
    return sys.prefix != sys.base_prefix


@dataclass
class CmdResult:
    code: int
    stdout: str


def run_command(cmd: str, cwd: str | None = None, fatal: bool = True, capture_output: bool = False) -> CmdResult:
    """Run the given command command.

    cwd: directory to run command in; defaults to WEST_TOPDIR;
    fatal: if True, program will terminate on command failure;
           if False, error is returned;
    capture_output: if True, stdout will be returned as string;
                    if False, stdout is piped and an empty string is returned;

    Only OS agnostic commands (such as git, python or west) should be used.
    """
    if cwd is None:
        cwd = WEST_TOPDIR

    try:
        log.inf(f"Running `{cmd}` in `{cwd}`", colorize=True)
        out = subprocess.run(  # noqa: S602
            cmd,
            shell=True,
            cwd=cwd,
            capture_output=capture_output,
            text=True,
            check=True,
            env=os.environ,
        )
        stdout: str = ""
        if out.stdout:
            stdout = out.stdout.strip()
            log.inf(stdout)
        return CmdResult(0, stdout)
    except FileNotFoundError:
        log.die(f"Invalid working directory {cwd}")
    except subprocess.CalledProcessError as e:
        if fatal:
            log.die(f"Cmd failed: {e}")
        else:
            log.wrn(f"Cmd failed: {e}")
            return CmdResult(e.returncode, e.stderr)


def install_system_packages(packages: list[str]) -> None:
    if sys.platform.startswith("linux"):
        exe = "sudo apt install"
    elif sys.platform.startswith("win"):
        log.die("Don't know how to install packages on windows.")
    else:
        msg: str = f"Unsupported platform: {sys.platform}"
        raise NotImplementedError(msg)

    run_command(" ".join([exe, *packages]))


def source_environment(env_file_path: str) -> None:
    load_dotenv(env_file_path)
    # Print all environment variables containing the words "zephyr", "west", or other interesting keywords:
    for key, value in os.environ.items():
        if any(keyword in key.lower() for keyword in ["zephyr", "west", "board"]):
            log.inf(f"{key}: {value}")


WEST_TOPDIR: str = run_command("west topdir", cwd=".", capture_output=True).stdout
