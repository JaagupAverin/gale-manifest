import argparse
import os
import sys
import textwrap
from pathlib import Path
from typing import Any, override

from projects import PROJECTS, Project, ProjectType
from util import in_venv, install_system_packages, run_command
from west import log
from west.commands import WestCommand

this_repo_dir = Path(__file__).parent.parent
sys.path.append(os.fspath(this_repo_dir))


class GaleSetup(WestCommand):
    def __init__(self) -> None:
        super().__init__(
            "gale-setup",
            "install development dependencies for building, flashing, etc",
            "Install development dependencies for building, flashing, etc. Usage: west gale-setup",
        )

    @override
    def do_add_parser(self, parser_adder: Any) -> argparse.ArgumentParser:
        parser: argparse.ArgumentParser = parser_adder.add_parser(
            self.name,
            help=self.help,
            description=self.description,
        )
        return parser

    @override
    def do_run(self, args: argparse.Namespace, unknown: list[str]) -> None:
        if not in_venv():
            self.die("This script must be run from within a virtual environment.")

        requirements_path = Path(__file__).parent.parent / "requirements.txt"
        if not requirements_path.exists():
            self.die(f"requirements.txt not found at {requirements_path}")

        log.inf(f"Installing requirements from {requirements_path}...", colorize=True)
        cmd: str = f"{sys.executable} -m pip install -r {requirements_path}"
        run_command(cmd)

        log.inf("Installing dependencies for QEMU...", colorize=True)
        install_system_packages(["qemu-system", "qemu-user-static"])


class GaleCheckout(WestCommand):
    def __init__(self) -> None:
        super().__init__(
            "gale-checkout",
            "fetch and checkout a branch in all user (non-fork) repositories",
            textwrap.dedent("""
                Checkout the given branch in all user (non-fork) repositories.
                Useful during development when working with multiple repositories that should point to the same branch.
                Usage: west gale-checkout <branch>
            """),
        )

    @override
    def do_add_parser(self, parser_adder: Any) -> argparse.ArgumentParser:
        parser: argparse.ArgumentParser = parser_adder.add_parser(
            self.name,
            help=self.help,
            description=self.description,
        )
        parser.add_argument(
            "branch",
            help="branch to checkout",
        )
        return parser

    @override
    def do_run(self, args: argparse.Namespace, unknown: list[str]) -> None:
        branch = args.branch
        log.inf(f"Checking out branch '{branch}' in all gale repositories...", colorize=True)
        cmd: str = f"git fetch && git switch {branch} || git switch --track origin/{branch}"

        user_projects: list[Project] = [project for project in PROJECTS if not project.is_fork]
        for project in user_projects:
            run_command(cmd, cwd=project.path, fatal=False)


class GalePush(WestCommand):
    def __init__(self) -> None:
        super().__init__(
            "gale-push",
            "commit and push local changes in all user (non-fork) repositories",
            textwrap.dedent("""
                Commit and push local changes in all user (non-fork) repositories.
                Useful during development when working with multiple repositories.
                Usage: west gale-push <"message">
            """),
        )

    @override
    def do_add_parser(self, parser_adder: Any) -> argparse.ArgumentParser:
        parser: argparse.ArgumentParser = parser_adder.add_parser(
            self.name,
            help=self.help,
            description=self.description,
        )
        parser.add_argument(
            "message",
            help="commit message",
        )
        return parser

    @override
    def do_run(self, args: argparse.Namespace, unknown: list[str]) -> None:
        log.inf("Committing and pushing changes in all gale repositories...", colorize=True)
        cmd: str = f'git add . && git commit -m "{args.message}" && git push'

        user_projects: list[Project] = [project for project in PROJECTS if not project.is_fork]
        for project in user_projects:
            run_command(cmd, cwd=project.path, fatal=False)


class GaleEmulate(WestCommand):
    def __init__(self) -> None:
        super().__init__(
            "gale-emulate",
            "run the given application in QEMU",
            "Run the given application in QEMU. Usage: west gale-emulate <app>",
        )

    @override
    def do_add_parser(self, parser_adder: Any) -> argparse.ArgumentParser:
        parser: argparse.ArgumentParser = parser_adder.add_parser(
            self.name,
            help=self.help,
            description=self.description,
        )
        parser.add_argument(
            "application",
            choices=[project.name for project in PROJECTS if project.type == ProjectType.App],
        )
        return parser

    @override
    def do_run(self, args: argparse.Namespace, unknown: list[str]) -> None:
        if not in_venv():
            self.die("This script must be run from within a virtual environment.")
