from typing import TYPE_CHECKING

from gale import log
from gale.boards import Board
from gale.project_cache import BuildCache
from gale.projects import Project
from gale.util import CmdMode, run_command, source_environment

if TYPE_CHECKING:
    from pathlib import Path


class Build:
    def __init__(self, project: Project, board: Board) -> None:
        self.project: Project = project
        self.board: Board = board
        self.build_dir: Path = self.project.path / "build"

    def build_target(self, target: str, extra_args: str = "") -> BuildCache:
        source_environment(self.board.env)

        build_cmd = (
            "west build"
            + f" -s {self.project.path}"
            + f" -d {self.build_dir}"
            + f" -t {target}"
            + f" {extra_args}"
            + " -- "
            + " -G'Ninja'"
        )
        run_command(
            cmd=build_cmd,
            desc=f"Building target '{target}' for project '{self.project.name}:{self.board.name}'",
            mode=CmdMode.FOREGROUND,
        )
        return BuildCache(self.build_dir / target)

    def get_build_cache(self, target: str) -> BuildCache:
        source_environment(self.board.env)

        target_build_dir = self.build_dir / target
        if not BuildCache.exists(target_build_dir):
            log.fatal(f"Build cache for target '{target}' does not exist; run build first.")
        return BuildCache(target_build_dir)
