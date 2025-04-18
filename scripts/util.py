import subprocess
import sys
from dataclasses import dataclass

from west import log


def in_venv() -> bool:
    return sys.prefix != sys.base_prefix


@dataclass
class CmdResult:
    code: int
    stdout: str


def run_command(cmd: str, cwd: str | None = None, fatal: bool = True) -> CmdResult:
    """Run the given command command.

    cwd: directory to run command in; defaults to WEST_TOPDIR;
    fatal: if True, program will terminate on command failure;
           if False, error is returned;

    Only OS agnostic commands (such as git, python) should be used.
    """
    if cwd is None:
        cwd = WEST_TOPDIR

    try:
        log.inf(f"Running `{cmd}` in `{cwd}`", colorize=True)
        out = subprocess.run(  # noqa: S602
            cmd,
            shell=True,
            cwd=cwd,
            stdout=subprocess.PIPE,
            text=True,
            check=True,
        )
        out = out.stdout.strip()
        return CmdResult(0, out)
    except FileNotFoundError:
        log.die(f"Invalid working directory {cwd}")
    except subprocess.CalledProcessError as e:
        if fatal:
            log.err(e.stderr)
            log.die(f"Cmd failed: {e}")
        else:
            log.wrn(e.stderr)
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


WEST_TOPDIR: str = run_command("west topdir", cwd=".").stdout
