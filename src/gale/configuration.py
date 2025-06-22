from typing import TYPE_CHECKING

from gale.build_cache import BuildCache
from gale.data.boards import Board
from gale.data.projects import Project
from gale.util import CmdMode, run_command, source_environment

if TYPE_CHECKING:
    from pathlib import Path


class Configuration:
    def __init__(self, project: Project, board: Board) -> None:
        self.project: Project = project
        self.board: Board = board
        self._root_build_dir: Path = self.project.dir / "build"

    def get_triplet(self, target: str) -> str:
        """Triplet format: <project_name>:<board_name>:<target_name>."""
        return f"{self.project.name}:{self.board.name}:{target}"

    def build_target(self, target: str, extra_args: str = "") -> BuildCache:
        """Build the given target with this configuration, returning the build cache."""
        source_environment(self.board.env)

        build_cmd: str = (
            "west build"
            + f" -s {self.project.dir}"
            + f" -d {self._root_build_dir}"
            + f" -t {target}"
            + f" {extra_args}"
            + " -- "
            + " -G'Ninja'"
        )
        run_command(
            cmd=build_cmd,
            desc=f"Building target '{self.get_triplet(target)}'",
            mode=CmdMode.FOREGROUND,
        )
        return BuildCache(self.get_triplet(target), self._root_build_dir / target)

    def get_build_cache(self, target: str) -> BuildCache:
        """Return the build cache for the given target.

        Target must have been built first, otherwise an error is raised.
        """
        source_environment(self.board.env)

        target_build_dir: Path = self._root_build_dir / target
        return BuildCache(self.get_triplet(target), target_build_dir)
