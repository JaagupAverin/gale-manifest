from typing import TYPE_CHECKING

from gale import log
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
        self._build_args_file: Path = self._target_build_dir / "build_args.txt"

    def _save_build_args(self, build_args: list[str] | None) -> None:
        """Cache the latest build arguments for later rebuilds."""
        with self._build_args_file.open("w") as f:
            f.write(" ".join(build_args) if build_args else "")
            log.inf(f"Cached build arguments into {f.name}")

    def _load_cached_build_args(self) -> list[str]:
        """Load the cached build arguments for the target."""
        try:
            with self._build_args_file.open("r") as f:
                args = f.read().split()
                log.inf(f"Loaded build arguments from {f.name}: {args}")
                return args
        except FileNotFoundError:
            log.inf(f"Build arguments file not found: {self._build_args_file}")
            return []

    def build(
        self,
        extra_args: list[str] | None = None,
        *,
        load_extra_args_from_disk: bool = False,
        save_extra_args_to_disk: bool = False,
    ) -> BuildCache:
        """Build the target, returning the build cache.

        Caches any build arguments to disk for later rebuilds (see `load_extra_args_from_disk`).

        Args:
            extra_args: additional arguments to pass to 'west build';
            load_extra_args_from_disk: if set, loads the latest cached build arguments from disk
                (overrides any provided extra_args!);
        """
        source_environment(self.board.env)

        if extra_args is None:
            extra_args = []

        if load_extra_args_from_disk and save_extra_args_to_disk:
            # If both load and save are enabled, this would recursively keep adding the same build arguments;
            # However its not intended to be used like that:
            # Either `save` is enabled, in which case all previously cached arguments are overwritten.
            # Or `load` is enabled, in which case the previously cached arguments are loaded, but not re-saved.
            # TODO: Review this logic with fresh mind and then finish SCA.
            msg = "Cannot load and save build arguments simultaneously; would cause recursion."
            raise ValueError(msg)

        if load_extra_args_from_disk:
            extra_args = extra_args + self._load_cached_build_args()
        args: str = " ".join(extra_args) if extra_args else ""

        build_cmd: str = (
            "west build"
            + f" -s {self.target.parent_project.dir}"
            + f" -d {self._root_build_dir}"
            + f" -t {self.target.cmake_target}"
            + f" {args}"
        )
        run_command(
            cmd=build_cmd,
            desc=f"Building target '{self.target.name}' for board '{self.board.name}'",
            mode=CmdMode.FOREGROUND,
        )

        if save_extra_args_to_disk:
            self._save_build_args(extra_args)

        build_cache: BuildCache = self.get_build_cache()
        self.target.post_build(build_cache)
        return build_cache

    def get_build_cache(self) -> BuildCache:
        """Return the build cache for a previously built target.

        Target must have been built first (cache files must exist on disk), otherwise an error is raised.
        """
        source_environment(self.board.env)
        return BuildCache(self.board, self.target, self._target_build_dir)
