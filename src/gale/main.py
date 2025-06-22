import os
from typing import Annotated

import typer

from gale import log
from gale.common import set_verbose
from gale.configuration import Configuration
from gale.data.boards import get_board
from gale.data.paths import BSIM_DIR
from gale.data.projects import PROJECTS, ZEPHYR_PROJECT, get_project
from gale.data.structs import BuildCache, Project, Target
from gale.data.targets import get_target
from gale.typer_args import BoardArg, ExtraArgs, ProjectArg, TargetArg
from gale.util import CmdMode, in_venv, run_command

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
def cmake(
    board: BoardArg,
    project: ProjectArg,
    cmake_target: str,
    extra_build_args: ExtraArgs = None,
) -> None:
    """Build a custom CMake target (one not provided by the pre-defined Targets), for the given board.

    This command is for testing and developing non-hardcoded-targets such as 'help'.
    """
    prj: Project = get_project(project)
    trgt: Target = Target(
        name=cmake_target,
        parent_project=prj,
        cmake_target=cmake_target,
    )

    conf: Configuration = Configuration(get_board(board), trgt)
    conf.build(extra_build_args)


@app.command(no_args_is_help=True)
def build(
    board: BoardArg,
    target: TargetArg,
    extra_build_args: ExtraArgs = None,
) -> None:
    """Build the given target, for the given board."""
    trgt: Target = get_target(target)

    conf: Configuration = Configuration(get_board(board), trgt)
    conf.build(extra_build_args)


@app.command(no_args_is_help=True)
def run(
    board: BoardArg,
    target: TargetArg,
    extra_run_args: ExtraArgs = None,
) -> None:
    """Run the given target, for the given board."""
    trgt: Target = get_target(target)
    if not trgt.run_callback:
        log.fatal(f"Target '{trgt.name}' does not support running.")

    conf: Configuration = Configuration(get_board(board), trgt)
    cache: BuildCache = conf.get_build_cache()
    trgt.run_callback(cache, extra_run_args)


@app.command(no_args_is_help=True)
def debug(
    board: BoardArg,
    target: TargetArg,
    extra_debug_args: ExtraArgs = None,
) -> None:
    """Debug the given target, for the given board."""
    trgt: Target = get_target(target)
    if not trgt.debug_callback:
        log.fatal(f"Target '{trgt.name}' does not support debugging.")

    conf: Configuration = Configuration(get_board(board), trgt)
    cache: BuildCache = conf.get_build_cache()
    trgt.debug_callback(cache, extra_debug_args)


if __name__ == "__main__":
    app()


# TODO1: Figure out how to prevent bsim from spamming output to primary console!
# TODO3: Look into build targets - think sysbuild is changing things up already?
# TODO4: Look into real-time bsim:
# https://docs.nordicsemi.com/bundle/ncs-latest/page/zephyr/boards/native/nrf_bsim/doc/nrf52_bsim.html#about_time_in_babblesim
