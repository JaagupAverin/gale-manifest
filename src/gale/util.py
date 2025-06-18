import os
import pty
import shlex
import signal
import subprocess
import sys
from dataclasses import dataclass, field
from enum import Enum
from functools import cache
from pathlib import Path
from threading import Semaphore, Thread
from typing import Any, Never

from dotenv import load_dotenv

from gale import log


def in_venv() -> bool:
    return sys.prefix != sys.base_prefix


@dataclass
class Cmd:
    ready: Semaphore = field(default_factory=Semaphore)
    thread: Thread | None = field(default=None)
    proc: subprocess.Popen[str] | None = field(default=None)
    cmd: str = field(default="")

    code: int = field(default=0)
    stdout: str = field(default="")


_CMD_HISTORY: list[Cmd] = []


class CmdMode(Enum):
    FOREGROUND = 0  # Run program with stdout/stdin piped to active terminal;
    BACKGROUND = 1  # Run program with stdout/stdin piped to a new virtual port;
    CAPTURE_RESULT = 2  # Run program without live stdout/stdin - only return result;
    REPLACE = 3  # Terminate Python and replace the terminal with the given command;


def run_command(
    cmd: str,
    desc: str,
    mode: CmdMode,
    cwd: Path | None = None,
    fatal: bool = True,
) -> Cmd:
    """Run the given command.

    cmd: command string, e.g "apt install python";
    desc: human readable description of what the command is doing;
    mode: determines how the command is run and how the result is handled; see enum;
    cwd: directory to run command in; defaults to WEST_TOPDIR;
    fatal: if True, program will terminate on command failure;
           if False, error is returned.
    Only OS agnostic commands (such as git, python or west) should be used.
    """
    if cwd is None:
        cwd = get_west_topdir()

    result = Cmd()
    result.cmd = cmd

    _CMD_HISTORY.append(result)

    pipe: int | None = 0
    if mode == CmdMode.BACKGROUND:
        pipe, slave_fd = pty.openpty()
        slave_name = os.ttyname(slave_fd)
        log.inf(
            f"Running command in background ({slave_name}).",
            desc=desc,
            cmd=cmd,
            cwd=str(cwd.absolute()),
            monitor=f"while true; do picocom --quiet {slave_name} || sleep 5; done",
        )
    elif mode == CmdMode.FOREGROUND:
        pipe = None
        log.inf("Running command in foreground.", desc=desc, cmd=cmd, cwd=cwd)
    elif mode == CmdMode.REPLACE:
        # This will terminate the current Python process, and instead pass the path and environment
        # to the new process that shall inherit this terminal. This is required for cases where
        # Python causes issues as the middle-man (e.g. catching interrupt signals, etc).
        log.inf("Running command in foreground (replacing Python!).", desc=desc, cmd=cmd, cwd=cwd)
        args = shlex.split(cmd)
        os.chdir(cwd)
        os.execve(args[0], args, os.environ)  # noqa: S606
        return None
    else:
        log.dbg("Running command for its stdout value.", cmd=cmd)
        pipe = subprocess.PIPE

    def run() -> None:
        with result.ready:
            try:
                result.proc = subprocess.Popen(  # noqa: S602
                    cmd,
                    shell=True,
                    cwd=cwd,
                    text=True,
                    stdout=pipe,
                    stderr=pipe,
                    stdin=pipe,
                    env=os.environ,
                )
                stdout, stderr = result.proc.communicate()
                result.proc.wait()
                result.code = result.proc.returncode

                if result.code == 0:
                    result.stdout = stdout.strip() if stdout else f"code {result.code}"
                elif result.code in (-signal.SIGINT, -signal.SIGTERM):
                    log.wrn(f"Command `{result.cmd}` was terminated")
                else:
                    result.stdout = stderr.strip() if stderr else f"code {result.code}"
                    if fatal:
                        log.fatal(f"Cmd `{result.cmd}` failed: {result.stdout}")

            except FileNotFoundError:
                log.fatal(f"Invalid working directory {cwd}")

    result.thread = Thread(target=run)
    result.thread.start()

    if mode == CmdMode.BACKGROUND:
        return result
    result.thread.join()
    return result


def _cleanup(signal_number: int, _frame: Any) -> Never:  # noqa: ANN401
    log.wrn(f"Received signal {signal_number}. Terminating ongoing processes...")
    # Terminate in reverse order since newer commands may depend on older ones:
    for cmd in reversed(_CMD_HISTORY):
        if cmd.proc and cmd.proc.poll() is None:
            try:
                cmd.proc.wait(0.1)
            except subprocess.TimeoutExpired:
                cmd.proc.send_signal(signal.SIGTERM)
                cmd.proc.wait(0.1)

        if cmd.thread:
            cmd.thread.join()
    sys.exit(0)


signal.signal(signal.SIGINT, _cleanup)


def install_system_packages(packages: list[str]) -> None:
    if sys.platform.startswith("linux"):
        exe = "sudo apt install"
    elif sys.platform.startswith("win"):
        log.fatal("Don't know how to install packages on windows.")
    else:
        msg: str = f"Unsupported platform: {sys.platform}"
        raise NotImplementedError(msg)

    run_command(
        cmd=" ".join([exe, *packages]),
        desc=f"Installing system packages: {packages}",
        mode=CmdMode.FOREGROUND,
    )


def source_environment(env_file_path: Path) -> None:
    load_dotenv(env_file_path)
    # Print all environment variables containing the words "zephyr", "west", or other interesting keywords:
    for key, value in os.environ.items():
        if any(keyword in key.lower() for keyword in ["zephyr", "west", "board"]):
            log.inf(f"{key}: {value}")


@cache
def get_west_topdir() -> Path:
    return Path(
        run_command(
            cmd="west topdir",
            desc="Determining WEST_TOPDIR",
            mode=CmdMode.CAPTURE_RESULT,
            cwd=Path(),
        ).stdout
    )


@cache
def get_manifest_dir() -> Path:
    return Path(f"{get_west_topdir()}/gale")


@cache
def get_projects_dir() -> Path:
    return Path(f"{get_manifest_dir()}/projects")


@cache
def get_tools_dir() -> Path:
    return Path(f"{get_projects_dir()}/tools")


@cache
def get_bsim_dir() -> Path:
    return Path(f"{get_tools_dir()}/bsim")
