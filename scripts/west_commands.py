import argparse
import os
import subprocess
import sys
import textwrap
from pathlib import Path
from typing import Any, override

from west import log
from west.commands import WestCommand

this_repo_dir = Path(__file__).parent.parent
sys.path.append(os.fspath(this_repo_dir))


def in_venv() -> bool:
    return sys.prefix != sys.base_prefix


class GaleInstall(WestCommand):
    def __init__(self) -> None:
        super().__init__(
            "gale-install",
            "install gale dependencies",
            "Install requirements for Gale development. Usage: west gale-install",
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
        else:
            log.inf(f"Installing requirements from {requirements_path}...", colorize=True)
            try:
                cmd: str = f"{sys.executable} -m pip install -r {requirements_path}"
                subprocess.check_call(cmd, shell=True)  # noqa: S602
            except subprocess.CalledProcessError as e:
                self.die(f"Failed to install requirements: {e}")


def run_command_for_all_repos(subcmd: str, group: str = "gale") -> None:
    try:
        cmd = f"west forall -g {group} -c '{subcmd}'"
        subprocess.check_call(cmd, shell=True)  # noqa: S602

        # Also repeat command for this (manifest) repository:
        log.inf(f"=== running '{subcmd}' in {this_repo_dir}", colorize=True)
        subprocess.check_call(subcmd, shell=True, cwd=this_repo_dir)  # noqa: S602
    except subprocess.CalledProcessError as e:
        log.wrn(f"Cmd failed: {e}")


class GaleCheckout(WestCommand):
    def __init__(self) -> None:
        super().__init__(
            "gale-checkout",
            "fetch and checkout the main branch in all gale repositories",
            textwrap.dedent("""
                Checkout the main (or custom) branch in all gale repositories.
                Useful during development when working with multiple repositories that should point to the same branch.
                Usage: west gale-checkout [<branch>]
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
            nargs="?",
            default="main",
            help="branch to checkout (default: main)",
        )
        return parser

    @override
    def do_run(self, args: argparse.Namespace, unknown: list[str]) -> None:
        branch = args.branch
        log.inf(f"Checking out branch '{branch}' in all gale repositories...", colorize=True)

        subcmd = f"git fetch && git switch {branch} || git switch --track origin/{branch}"
        run_command_for_all_repos(subcmd)


class GalePush(WestCommand):
    def __init__(self) -> None:
        super().__init__(
            "gale-push",
            "commit and push local changes in all gale repositories",
            textwrap.dedent("""
                Commit and push local changes in all gale repositories.
                Useful during development when working with multiple repositories.
                Usage: west gale-push [message]
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
            nargs="?",
            default="Update",
        )
        return parser

    @override
    def do_run(self, args: argparse.Namespace, unknown: list[str]) -> None:
        log.inf("Committing and pushing changes in all gale repositories...", colorize=True)

        subcmd = f'git diff-index --quiet HEAD -- || git add . && git commit -m "{args.message}" && git push || true'
        run_command_for_all_repos(subcmd)
