import os
from typing import TYPE_CHECKING, Annotated

import typer

from gale import log
from gale.common import set_verbose
from gale.configuration import Configuration
from gale.data.boards import get_board
from gale.data.paths import BSIM_DIR
from gale.data.projects import PROJECTS, ZEPHYR_PROJECT, get_project
from gale.data.targets import RawTarget, get_target
from gale.typer_args import (
    BaudrateArg,
    BoardArg,
    ExtraBuildArgs,
    GdbArg,
    PortArg,
    ProjectArg,
    RealTimeArg,
    RebuildArg,
    TargetArg,
)
from gale.util import CmdMode, in_venv, run_command, serial_monitor

if TYPE_CHECKING:
    from gale.data.structs import BuildCache, Project, Target

app: typer.Typer = typer.Typer(name="woid", rich_markup_mode="rich", no_args_is_help=True)


class CommandPanel:
    GIT: str = "Git / Version control"
    PROJECT_DEVELOPMENT: str = "Project development"
    OTHER: str = "Other"


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


@app.command(rich_help_panel=CommandPanel.GIT)
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


@app.command(rich_help_panel=CommandPanel.GIT)
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


@app.command(no_args_is_help=True, rich_help_panel=CommandPanel.PROJECT_DEVELOPMENT)
def build(
    board: BoardArg,
    target: TargetArg,
    extra_build_args: ExtraBuildArgs = None,
) -> None:
    """Build the given target, for the given board."""
    trgt: Target = get_target(target)

    conf: Configuration = Configuration(get_board(board), trgt)
    conf.build(extra_build_args)


@app.command(no_args_is_help=True, rich_help_panel=CommandPanel.PROJECT_DEVELOPMENT)
def run(
    board: BoardArg,
    target: TargetArg,
    rebuild: RebuildArg = False,
    gdb: GdbArg = False,
    real_time: RealTimeArg = False,
) -> None:
    """Run the given target, for the given board."""
    trgt: Target = get_target(target)
    conf: Configuration = Configuration(get_board(board), trgt)
    cache: BuildCache = conf.build() if rebuild else conf.get_build_cache()
    trgt.run(cache, gdb=gdb, real_time=real_time)


@app.command(no_args_is_help=True, rich_help_panel=CommandPanel.PROJECT_DEVELOPMENT)
def monitor(
    port: PortArg,
    baud: BaudrateArg = 115200,
    new_terminal: Annotated[bool, typer.Option(help="Spawn a new terminal window for the monitor")] = False,
) -> None:
    """Monitor an already running device; i.e. attach to the given port for shell or console."""
    serial_monitor(port=port, baud=baud, spawn_new_terminal=new_terminal)


@app.command(no_args_is_help=True, rich_help_panel=CommandPanel.PROJECT_DEVELOPMENT)
def cmake(
    board: BoardArg,
    project: ProjectArg,
    cmake_target: Annotated[str, typer.Argument(help="The CMake target to build, e.g. 'help'", show_default=False)],
    extra_build_args: ExtraBuildArgs = None,
) -> None:
    """Build a custom CMake target (one not provided by the pre-defined Targets), for the given board.

    This command is for testing and developing non-hardcoded-targets such as 'help'.
    """
    prj: Project = get_project(project)
    trgt: Target = RawTarget(
        name=cmake_target,
        parent_project=prj,
        cmake_target=cmake_target,
    )

    conf: Configuration = Configuration(get_board(board), trgt)
    conf.build(extra_build_args)


@app.command(rich_help_panel=CommandPanel.OTHER)
def setup() -> None:
    """Install development dependencies for building, flashing, etc. Called once after cloning the workspace.

    Usage: gale setup
    """
    # Build BabbleSim:
    run_command(
        cmd="make everything -j 8",
        desc="Building BabbleSim",
        mode=CmdMode.FOREGROUND,
        cwd=BSIM_DIR,
    )


if __name__ == "__main__":
    app()


# TODO: get the fk shell working
# TODO: flash.bin is being created, but writing to it broke? Get it working again!
# BIG TODO: Get mcuboot working with flash.bin and sysbuild
