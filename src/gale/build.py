from typing import TYPE_CHECKING, Self, TypeGuard

from gale.boards import Board
from gale.project_cache import ProjectCache
from gale.projects import Project
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
        return (
            "west build"
            + f" -s {self.project.path}"
            + f" -d {self.build_dir}"
            + f" {extra_args} "
            + " -- "
            + " -G'Ninja'"
        )

    def generate_cmake(self) -> ProjectCache:
        source_environment(self.board.env)

        generate_cmd: str = self._build_cmd("--cmake-only")
        run_command(
            cmd=generate_cmd,
            desc=f"Generating CMake for project '{self.project.name}:{self.board.name}'",
            mode=CmdMode.FOREGROUND,
        )
        self.project_cache = ProjectCache(self.build_dir)
        return self.project_cache

    def build_target(self, target: str) -> ProjectCache:
        source_environment(self.board.env)

        build_cmd: str = self._build_cmd(f"-t {target}")
        run_command(
            cmd=build_cmd,
            desc=f"Building target '{target}' for project '{self.project.name}:{self.board.name}'",
            mode=CmdMode.FOREGROUND,
        )
        self.project_cache = ProjectCache(self.build_dir / target)
        return self.project_cache
