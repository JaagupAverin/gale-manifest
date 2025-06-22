from typing import TYPE_CHECKING

from gale.data.structs import Board, BuildCache, Target
from gale.util import CmdMode, run_command, source_environment

if TYPE_CHECKING:
    from pathlib import Path


class Configuration:
    def __init__(self, board: Board, target: Target) -> None:
        self.board: Board = board
        self.target: Target = target
        self._root_build_dir: Path = self.target.parent_project.dir / "build"
        subdir: str = self.target.build_subdir if self.target.build_subdir else ""
        self._target_build_dir: Path = self._root_build_dir / subdir

    def build(self, extra_args: list[str] | None = None) -> BuildCache:
        """Build the target, returning the build cache."""
        source_environment(self.board.env)
        args: str = " ".join(extra_args) if extra_args else ""

        build_cmd: str = (
            "west build"
            + f" -s {self.target.parent_project.dir}"
            + f" -d {self._root_build_dir}"
            + f" -t {self.target.cmake_target}"
            + f" {args}"
            + " -- "
            + " -G'Ninja'"
        )
        run_command(
            cmd=build_cmd,
            desc=f"Building target '{self.target.name}' for board '{self.board.name}'",
            mode=CmdMode.FOREGROUND,
        )

        build_cache: BuildCache = self.get_build_cache()
        if self.target.post_build_handler:
            self.target.post_build_handler(build_cache)
        return build_cache

    def get_build_cache(self) -> BuildCache:
        """Return the build cache for a previously built target.

        Target must have been built first (cache files must exist on disk), otherwise an error is raised.
        """
        source_environment(self.board.env)
        return BuildCache(self.board, self.target, self._target_build_dir)
