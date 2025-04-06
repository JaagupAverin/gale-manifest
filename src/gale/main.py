from enum import Enum
from typing import Annotated

import typer

from gale import log
from gale.common import set_verbose
from gale.projects import HMI_APP_PROJECT, PROJECTS, SENSOR_APP_PROJECT, SHARED_PROJECT, Project
from gale.util import in_venv, install_system_packages, run_command, source_environment

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

    if ctx.invoked_subcommand:
        log.dbg(f"Running command `{ctx.invoked_subcommand}`.")


@app.command()
def setup() -> None:
    """Install development dependencies for building, flashing, etc.

    Usage: gale setup
    """
    if not in_venv():
        log.fatal("This script must be run from within a virtual environment.")

    log.inf("Installing dependencies for QEMU...")
    install_system_packages(["qemu-system", "qemu-user-static"])


@app.command()
def checkout(branch: str) -> None:
    """Checkout the given branch in all user (non-fork) repositories.

    Useful during development when working with multiple repositories that should point to the same branch.
    Usage: gale checkout <branch>
    """
    log.inf(f"Checking out branch '{branch}' in all gale repositories...")
    cmd: str = f"git fetch && git switch {branch} || git switch --track origin/{branch}"

    user_projects: list[Project] = [project for project in PROJECTS if not project.is_fork]
    for project in user_projects:
        run_command(cmd, cwd=project.path, fatal=False)


@app.command()
def push(message: str) -> None:
    """Commit and push local changes in all user (non-fork) repositories.

    Useful during development when working with multiple repositories.
    Usage: gale push <message>
    """
    log.inf("Committing and pushing changes in all gale repositories...")
    cmd: str = f'git add . && git commit -m "{message}" && git push'

    user_projects: list[Project] = [project for project in PROJECTS if not project.is_fork]
    for project in user_projects:
        run_command(cmd, cwd=project.path, fatal=False)


class AppEnum(str, Enum):
    HMI_APP = "hmi"
    SENSOR_APP = "sensor"


@app.command()
def emulate(app: AppEnum) -> None:
    """Run the given application in QEMU. Usage: gale emulate <app>."""
    if not in_venv():
        log.fatal("This script must be run from within a virtual environment.")

    project: Project | None = None
    if app == AppEnum.HMI_APP:
        project = HMI_APP_PROJECT
    elif app == AppEnum.SENSOR_APP:
        project = SENSOR_APP_PROJECT

    # Source the environment file, which exports the QEMU board value, etc:
    env_qemu: str = f"{SHARED_PROJECT.path}/env_qemu"
    source_environment(env_qemu)

    # Build the application for the QEMU board and run the "flash" command:
    build_dir: str = f"{project.path}/build_qemu"
    run_command(f"west build -d {build_dir} -t run", cwd=project.path)


if __name__ == "__main__":
    app()
