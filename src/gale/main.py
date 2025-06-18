import os
from pathlib import Path
from typing import TYPE_CHECKING, Annotated

import typer

from gale import log
from gale.boards import BoardEnum, get_board
from gale.build import Build
from gale.common import set_verbose
from gale.projects import PROJECTS, ZEPHYR_PROJECT, Project, ProjectEnum, get_project
from gale.util import CmdMode, get_bsim_dir, in_venv, run_command

if TYPE_CHECKING:
    from gale.project_cache import BuildCache

app: typer.Typer = typer.Typer(name="woid", rich_markup_mode="rich", no_args_is_help=True)


@app.callback(invoke_without_command=True)
def gale(
    ctx: typer.Context,
    verbose: Annotated[
        bool,
        typer.Option(
            "--verbose",
            "-v",
            help="Print out debug-level messages.",
        ),
    ] = False,
) -> None:
    """Workspace management tool for Gale."""
    if verbose:
        set_verbose(True)

    os.environ["ZEPHYR_BASE"] = str(ZEPHYR_PROJECT.path.absolute())

    if not in_venv():
        log.fatal("This tool must be run from within a virtual environment; create and activate .venv as per README!")

    if ctx.invoked_subcommand:
        log.dbg(f"Running command `{ctx.invoked_subcommand}`.")


@app.command()
def setup() -> None:
    """Install development dependencies for building, flashing, etc.

    Usage: gale setup
    """
    run_command(
        cmd="make everything -j 8",
        desc="Building BabbleSim",
        mode=CmdMode.FOREGROUND,
        cwd=get_bsim_dir(),
    )


@app.command()
def checkout(branch: str) -> None:
    """Checkout the given branch in all user (non-fork) repositories.

    Useful during development when working with multiple repositories that should point to the same branch.
    Usage: gale checkout <branch>
    """
    cmd: str = f"git fetch && git switch {branch} || git switch --track origin/{branch}"

    user_projects: list[Project] = [project for project in PROJECTS if not project.is_fork]
    for project in user_projects:
        run_command(
            cmd=cmd,
            desc=f"Checking out branch '{branch}' in project '{project.name}'",
            mode=CmdMode.FOREGROUND,
            cwd=project.path,
            fatal=False,
        )


@app.command()
def push(message: str) -> None:
    """Commit and push local changes in all user (non-fork) repositories.

    Useful during development when working with multiple repositories.
    Usage: gale push <message>
    """
    cmd: str = f'git add . && git commit -m "{message}" && git push'

    user_projects: list[Project] = [project for project in PROJECTS if not project.is_fork]
    for project in user_projects:
        run_command(
            cmd=cmd,
            desc=f"Commiting and pushing changes in project '{project.name}'",
            mode=CmdMode.FOREGROUND,
            cwd=project.path,
            fatal=False,
        )


@app.command()
def build(
    project: ProjectEnum,
    board: BoardEnum,
    target: str,
    extra_args: Annotated[list[str], typer.Argument(help="Extra arguments to pass to 'west build'")],
) -> None:
    """Build the given target. Usage: gale build <project> <board> <target> [-- <extra_args>]."""
    build: Build = Build(get_project(project), get_board(board))
    build.build_target(target, " ".join(extra_args))


@app.command()
def run(
    project: ProjectEnum,
    board: BoardEnum,
    target: str,
    extra_args: Annotated[list[str] | None, typer.Argument(help="Extra arguments to pass to the runner")] = None,
) -> None:
    """Run the given target. Usage: gale run <project> <board> <target> [-- <extra_args>]."""
    build: Build = Build(get_project(project), get_board(board))
    cache: BuildCache = build.get_build_cache(target)

    if build.board.is_bsim:
        exe = Path(cache.cmake_cache.exe_path)
        if not exe.exists():
            log.fatal(f"Output binary '{exe}' does not exist; use build first.")

        extra = " ".join(extra_args) if extra_args else ""
        run_cmd = f"{exe} -nosim {extra}"
        # TODO1: Figure out how to prevent bsim from spamming output to primary console!
        run_command(run_cmd, desc=f"Running '{target}' natively", mode=CmdMode.REPLACE)
    else:
        log.fatal("Direct running on board not yet implemented.")


@app.command()
def debug(
    project: ProjectEnum,
    board: BoardEnum,
    target: str,
) -> None:
    """Debug the given target. Usage: gale debug <project> <board> <target>."""
    build: Build = Build(get_project(project), get_board(board))
    cache: BuildCache = build.get_build_cache(target)

    if build.board.is_bsim:
        exe = Path(cache.cmake_cache.exe_path)
        if not exe.exists():
            log.fatal(f"Output binary '{exe}' does not exist; use build first.")

        dbg_cmd = f"{cache.cmake_cache.gdb} --tui --args {exe} -nosim -uart1_pty_attach"
        # TODO2: Test out this with the new REPLACE command: is --tui still causing issues?
        run_command(dbg_cmd, desc=f"Debugging '{target}' natively", mode=CmdMode.REPLACE)
    else:
        log.fatal("Direct running on board not yet implemented.")


if __name__ == "__main__":
    app()

    # TODO3: Look into build targets - think sysbuild is changing things up already?
    # TODO4: Look into real-time bsim: https://docs.nordicsemi.com/bundle/ncs-latest/page/zephyr/boards/native/nrf_bsim/doc/nrf52_bsim.html#about_time_in_babblesim
