import os
from typing import TYPE_CHECKING

from rich import print_json

from gale import log
from gale.boards import Board
from gale.project_cache import ProjectCache
from gale.projects import ZEPHYR_PROJECT, Project
from gale.util import CmdMode, run_command, source_environment

if TYPE_CHECKING:
    from pathlib import Path


class Build:
    def __init__(self, project: Project, board: Board) -> None:
        self.project: Project = project
        self.board: Board = board
        self.build_dir: Path = self.project.path / "build"
        self.project_cache: ProjectCache | None = None

    def _build_cmd(self, extra_args: str) -> str:
        extra_conf = f" --extra-conf {self.board.prj_conf}" if self.board.prj_conf else ""
        extra_dtc_overlay = f" --extra-dtc-overlay {self.board.overlay}" if self.board.overlay else ""
        return (
            "west build"
            + f" -s {self.project.path}"
            + f" -d {self.build_dir}"
            + extra_conf
            + extra_dtc_overlay
            + f" {extra_args} "
            + " -- "
            + " -G'Ninja'"
        )

    def source_env(self) -> None:
        os.environ["ZEPHYR_BASE"] = str(ZEPHYR_PROJECT.path.absolute())
        source_environment(self.board.env)

    def generate_cmake(self) -> None:
        self.source_env()

        generate_cmd: str = self._build_cmd("--cmake-only")
        run_command(
            cmd=generate_cmd,
            desc=f"Generating CMake for project '{self.project.name}:{self.board.name}'",
            mode=CmdMode.FOREGROUND,
        )
        self.project_cache = ProjectCache(self.build_dir)

    def build_target(self, target: str) -> None:
        self.source_env()

        build_cmd: str = self._build_cmd(f"-t {target}")
        run_command(
            cmd=build_cmd,
            desc=f"Building target '{target}' for project '{self.project.name}:{self.board.name}'",
            mode=CmdMode.FOREGROUND,
        )
        self.project_cache = ProjectCache(self.build_dir)
