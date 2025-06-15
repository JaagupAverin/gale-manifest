import os
from pathlib import Path
from typing import Annotated

import typer

from gale import log
from gale.boards import BoardEnum, get_board
from gale.build import Build
from gale.common import set_verbose
from gale.project_cache import ProjectCache
from gale.projects import PROJECTS, SHARED_PROJECT, ZEPHYR_PROJECT, Project, ProjectEnum, get_project
from gale.util import CmdMode, get_bsim_dir, in_venv, run_command

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
) -> None:
    """Build the given target. Usage: gale build <project> <board> <target>."""
    build: Build = Build(get_project(project), get_board(board))
    build.build_target(target)


@app.command()
def run(
    project: ProjectEnum,
    board: BoardEnum,
    target: str,
    debug: Annotated[bool, typer.Option("--debug", help="Enable debug server.")] = False,
) -> None:
    build: Build = Build(get_project(project), get_board(board))
    cache = build.build_target(target)

    # TODO1: Fix debugging.
    # TODO2: Reduce excessive generation and build if not needed.
    # TODO3: Look into build targets - think sysbuild is changing things up already?
    # TODO4: Look into real-time bsim: https://docs.nordicsemi.com/bundle/ncs-latest/page/zephyr/boards/native/nrf_bsim/doc/nrf52_bsim.html#about_time_in_babblesim
    if build.board.is_bsim:
        exe = f"{cache.cmake_cache.native_executable} -nosim"
        run_command(f"{exe}", desc="Running built executable natively.", mode=CmdMode.FOREGROUND)
    else:
        pass
        # Flash...

    return
    if debug:
        project_cache: ProjectCache = ProjectCache(Path(build_dir))
        gdb: str = project_cache.cmake_cache.gdb
        zephyr_base: str = project_cache.cmake_cache.zephyr_base
        run_command(command, mode=CmdMode.BACKGROUND, cwd=project.path)

        elf_path = f"{build_dir}/zephyr/zephyr.elf"
        gdbconf = f"-x {SHARED_PROJECT.path}/gdb/.qemu_gdbconf"
        prep_zephyr = f"-ex='dir {zephyr_base}'"
        run_command(
            f"{gdb} {prep_zephyr} {gdbconf} {elf_path}",
            mode=CmdMode.FOREGROUND,
        )
    else:
        run_command(command, mode=CmdMode.FOREGROUND, cwd=project.path)


if __name__ == "__main__":
    app()
