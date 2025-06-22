import os
import pty
import shlex
import signal
import subprocess
import sys
import textwrap
from dataclasses import dataclass, field
from enum import Enum
from functools import partial
from pathlib import Path
from threading import Semaphore, Thread
from typing import Any, Never

from dotenv import load_dotenv

from gale import log
from gale.build_cache import BuildCache
from gale.data.paths import GALE_ROOT_DIR
from gale.data.projects import MANIFEST_PROJECT


def in_venv() -> bool:
    return sys.prefix != sys.base_prefix


@dataclass
class CmdHandle:
    ready: Semaphore = field(default_factory=Semaphore)
    """Given when process finishes."""
    thread: Thread | None = field(default=None)
    """Thread running the command."""
    proc: subprocess.Popen[str] | None = field(default=None)
    """Process running the command."""
    cmd: str = field(default="")
    """Raw command being executed, i.e `west update`."""

    code: int = field(default=0)
    """Exit code of the command; only valid when `ready` is given."""
    stdout: str = field(default="")
    """Stdout or stderr of the command; only valid when `ready` is given."""


_CMD_HISTORY: list[CmdHandle] = []


class CmdMode(Enum):
    FOREGROUND = 0  # Run program with stdout/stdin piped to active terminal;
    BACKGROUND = 1  # Run program with stdout/stdin piped to a new virtual port;
    CAPTURE_RESULT = 2  # Run program without live stdout/stdin - only return result;
    REPLACE = 3  # Terminate Python and replace the terminal with the given command;


def _run_actual(
    cmd: str,
    cwd: Path,
    pipe: int | None,
    cmd_handle: CmdHandle,
) -> None:
    """Wrapper around a subprocess.

    When the process finishes, fills out the handle's code and stdout/stderr fields, and gives the ready semaphore.
    """
    with cmd_handle.ready:
        try:
            cmd_handle.proc = subprocess.Popen(  # noqa: S602
                cmd,
                shell=True,
                cwd=cwd,
                text=True,
                stdout=pipe,
                stderr=pipe,
                stdin=pipe,
                env=os.environ,
            )
            stdout, stderr = cmd_handle.proc.communicate()
            cmd_handle.proc.wait()
            cmd_handle.code = cmd_handle.proc.returncode

            if cmd_handle.code == 0:
                cmd_handle.stdout = stdout.strip() if stdout else f"code {cmd_handle.code}"
            elif cmd_handle.code in (-signal.SIGINT, -signal.SIGTERM):
                log.wrn(f"Command `{cmd_handle.cmd}` was terminated")
            else:
                cmd_handle.stdout = stderr.strip() if stderr else f"code {cmd_handle.code}"

        except FileNotFoundError:
            cmd_handle.code = 1
            cmd_handle.stdout = f"Invalid working directory {cwd}"


def run_command(
    *,  # Force all arguments to be keyword-typed for clarity and consistency.
    cmd: str,
    desc: str,
    mode: CmdMode,
    cwd: Path | None = None,
    fatal: bool = True,
) -> CmdHandle:
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
        cwd = GALE_ROOT_DIR

    cmd_handle = CmdHandle()
    cmd_handle.cmd = cmd

    _CMD_HISTORY.append(cmd_handle)

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
        args: list[str] = shlex.split(cmd)
        os.chdir(cwd)
        os.execve(args[0], args, os.environ)  # noqa: S606
    else:
        log.dbg("Running command for its stdout value.", cmd=cmd)
        pipe = subprocess.PIPE

    cmd_handle.thread = Thread(
        target=partial(
            _run_actual,
            cmd=cmd,
            cwd=cwd,
            pipe=pipe,
            cmd_handle=cmd_handle,
        )
    )
    cmd_handle.thread.start()

    if mode == CmdMode.BACKGROUND:
        return cmd_handle  # Caller is responsible for checking the code and stdout!

    # Otherwise wait for the command to finish:
    cmd_handle.thread.join()
    if fatal and cmd_handle.code != 0:
        log.fatal(f"Cmd `{cmd_handle.cmd}` failed: {cmd_handle.stdout}")
    return cmd_handle


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
    """A work-in-progress function to install system packages in OS-agnostic way."""
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


def generate_clangd_file(cache: BuildCache) -> None:
    """Writes a .clangd file for the given build cache in gale root directory, in order to benefit LSPs."""
    clangd_file_content = textwrap.dedent(f"""
    # This file is auto-generated by gale for the latest built target ({cache.triplet}).
    CompileFlags:
      CompilationDatabase: {cache.build_dir}
      Add: -Wno-unknown-warning-option
      Remove: [-m*, -f*]
    """)

    clangd_file_path = MANIFEST_PROJECT.dir / ".clangd"
    log.inf(f"Generating .clangd file at {clangd_file_path}")
    with clangd_file_path.open("w") as file:
        file.write(clangd_file_content)
