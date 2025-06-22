import os
from pathlib import Path
from typing import TYPE_CHECKING, Annotated

import typer

from gale import log
from gale.common import set_verbose
from gale.configuration import Configuration
from gale.data.boards import Board, get_board
from gale.data.paths import BSIM_DIR
from gale.data.projects import PROJECTS, ZEPHYR_PROJECT, Project
from gale.data.targets import Target, get_target
from gale.typer_args import BoardArg, ExtraArgs, ProjectArg, TargetArg
from gale.util import CmdMode, generate_clangd_file, in_venv, run_command

if TYPE_CHECKING:
    from gale.build_cache import BuildCache

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

    os.environ["ZEPHYR_BASE"] = str(ZEPHYR_PROJECT.dir.absolute())

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
        cwd=BSIM_DIR,
    )


@app.command()
def checkout(branch: str) -> None:
    """Checkout the given branch in all user repositories.

    Useful during development when working with multiple repositories that should point to the same branch.
    Usage: gale checkout <branch>
    """
    cmd: str = f"git fetch && git switch {branch} || git switch --track origin/{branch}"

    user_projects: list[Project] = [project for project in PROJECTS.values() if not project.upstream]
    for project in user_projects:
        run_command(
            cmd=cmd,
            desc=f"Checking out branch '{branch}' in project '{project.name}'",
            mode=CmdMode.FOREGROUND,
            cwd=project.dir,
            fatal=False,
        )


@app.command()
def push(message: str) -> None:
    """Commit and push local changes in all user repositories.

    Useful during development when working with multiple repositories.
    Usage: gale push <message>
    """
    cmd: str = f'git add . && git commit -m "{message}" && git push'

    user_projects: list[Project] = [project for project in PROJECTS.values() if not project.upstream]
    for project in user_projects:
        run_command(
            cmd=cmd,
            desc=f"Commiting and pushing changes in project '{project.name}'",
            mode=CmdMode.FOREGROUND,
            cwd=project.dir,
            fatal=False,
        )


@app.command(no_args_is_help=True)
def build(
    board: BoardArg,
    target: TargetArg,
    extra_build_args: ExtraArgs = None,
) -> None:
    """Build the given target."""
    board_actual: Board = get_board(board)
    target_actual: Target = get_target(target)
    args_actual: str = " ".join(extra_build_args) if extra_build_args else ""

    project: Project = target_actual.parent_project
    conf: Configuration = Configuration(project, board_actual)
    cache: BuildCache = conf.build_target(target_actual.cmake_target, args_actual)
    generate_clangd_file(cache)


@app.command(no_args_is_help=True)
def run(
    board: BoardArg,
    target: TargetArg,
    extra_run_args: ExtraArgs = None,
) -> None:
    """Run the given target."""
    board_actual: Board = get_board(board)
    target_actual: Target = get_target(target)
    args_actual: str = " ".join(extra_run_args) if extra_run_args else ""

    project: Project = target_actual.parent_project
    conf: Configuration = Configuration(project, board_actual)
    cache: BuildCache = conf.get_build_cache(target_actual.cmake_target)

    if conf.board.is_bsim:
        exe: Path = Path(cache.cmake_cache.exe_path)
        if not exe.exists():
            log.fatal(f"Output binary '{exe}' does not exist; use build first.")

        run_cmd: str = f"{exe} -nosim {args_actual}"
        run_command(
            cmd=run_cmd,
            desc=f"Running '{target}' natively",
            mode=CmdMode.REPLACE,
        )
    else:
        log.fatal("Direct running on board not yet implemented.")


@app.command(no_args_is_help=True)
def debug(
    board: BoardArg,
    target: TargetArg,
    extra_debug_args: ExtraArgs = None,
) -> None:
    """Debug the given target."""
    board_actual: Board = get_board(board)
    target_actual: Target = get_target(target)
    args_actual: str = " ".join(extra_debug_args) if extra_debug_args else ""

    project: Project = target_actual.parent_project
    conf: Configuration = Configuration(project, board_actual)
    cache: BuildCache = conf.get_build_cache(target_actual.cmake_target)

    if conf.board.is_bsim:
        exe: Path = Path(cache.cmake_cache.exe_path)
        if not exe.exists():
            log.fatal(f"Output binary '{exe}' does not exist; use build first.")

        run_cmd: str = f"{exe} -nosim {args_actual}"
        dbg_cmd: str = f"{cache.cmake_cache.gdb} --tui --args {run_cmd}"
        # TODO1: Figure out how to prevent bsim from spamming output to primary console!
        # TODO2: Test out this with the new REPLACE command: is --tui still causing issues?
        run_command(cmd=dbg_cmd, desc=f"Debugging '{target}' natively", mode=CmdMode.REPLACE)
    else:
        log.fatal("Direct debugging on board not yet implemented.")


if __name__ == "__main__":
    app()

    # TODO: Look into 'gale setup' creating some environment file that could be used by editors.
    # TODO3: Look into build targets - think sysbuild is changing things up already?
    # TODO4: Look into real-time bsim:
    # https://docs.nordicsemi.com/bundle/ncs-latest/page/zephyr/boards/native/nrf_bsim/doc/nrf52_bsim.html#about_time_in_babblesim
