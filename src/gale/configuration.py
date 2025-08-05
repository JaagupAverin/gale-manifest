from typing import TYPE_CHECKING

from gale import log
from gale.data.projects import SHARED_PROJECT
from gale.data.structs import Board, BuildCache, BuildType, Target, get_triplet
from gale.util import CmdMode, run_command

if TYPE_CHECKING:
    from pathlib import Path


class Configuration:
    def __init__(self, board: Board, target: Target, build_type: BuildType) -> None:
        self.board: Board = board
        self.target: Target = target
        self.build_type: BuildType = build_type
        self.triplet: str = get_triplet(board, target, build_type)
        self.root_build_dir: Path = self.target.parent_project.dir / "build" / self.triplet
        self.target_build_dir: Path = self.root_build_dir / self.target.build_subdir
        self._build_args_file: Path = self.target_build_dir / "build_args.txt"

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

    def _get_extra_args_for_build_type(self, build_type: BuildType) -> list[str]:
        if build_type == BuildType.SCA:
            codechecker_config: Path = SHARED_PROJECT.dir / "share/codechecker/.codechecker.json"
            codechecker_args: str = f"--skip={SHARED_PROJECT.dir}/share/codechecker/skipfile.txt "
            codechecker_args = codechecker_args.replace(" ", ";")  # Can't have spaces in args, semicolon is alternative
            sca_args: list[str] = [
                "-DZEPHYR_SCA_VARIANT=codechecker",
                f"-DCODECHECKER_NAME={self.target.name}",
                f"-DCODECHECKER_CONFIG_FILE={codechecker_config}",
                f"-DCODECHECKER_ANALYZE_OPTS='{codechecker_args}'",
                "-DCODECHECKER_PARSE_SKIP=1",
            ]
            return sca_args
        return []

    def build(
        self,
        extra_args: list[str] | None = None,
        *,
        pristine: bool = False,
        cmake_only: bool = False,
        load_extra_args_from_disk: bool = False,
        save_extra_args_to_disk: bool = False,
    ) -> BuildCache:
        """Build the target, returning the build cache.

        Caches any build arguments to disk for later rebuilds (see `load_extra_args_from_disk`).

        Args:
            extra_args: additional arguments to pass to cmake (i.e. 'west build -- <args>');
            build_dir_suffix: suffix to append to the build directory name;
            pristine: if set, passes the --pristine flag to 'west build';
            cmake_only: if set, passes the --cmake-only flag to 'west build';
            load_extra_args_from_disk: if set, loads the latest cached build arguments from disk
                (appended to `extra_args`);
            save_extra_args_to_disk: if set, saves the provided build arguments to disk for later rebuilds.
                (cannot be used together with `load_extra_args_from_disk`, as this could easily cause weird issues)
        """
        if load_extra_args_from_disk and save_extra_args_to_disk:
            msg = "Cannot load and save build arguments simultaneously; might cause the same arguments to build up."
            raise ValueError(msg)

        if extra_args is None:
            extra_args = []
        extra_args = extra_args + self._get_extra_args_for_build_type(self.build_type)

        if load_extra_args_from_disk:
            extra_args = extra_args + self._load_cached_build_args()
        args: str = " ".join(extra_args) if extra_args else ""

        self.target.pre_build(self.target_build_dir)
        build_cmd: str = (
            "west build"
            + f" -s {self.target.parent_project.dir}"
            + f" -d {self.root_build_dir}"
            + f" -t {self.target.cmake_target}"
            + f" -b {self.board.primary_board}"
            + " --sysbuild"  # In case of nrf-sdk, sysbuild is implied by default, but can still set explicitly.
            + (" --pristine" if pristine else "")
            + (" --cmake-only" if cmake_only else "")
            + " --"
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
        return BuildCache(self.board, self.target, self.build_type, self.target_build_dir)
