from __future__ import annotations

import re
from abc import ABC
from dataclasses import dataclass
from typing import TYPE_CHECKING

from gale import log

if TYPE_CHECKING:
    from pathlib import Path


@dataclass
class Board:
    name: str
    """Human readable name without any semantic meaning."""
    dir: Path
    """The directory where the board's environment file is located."""

    @property
    def env(self) -> Path:
        file = self.dir / "environment"
        if not file.exists():
            log.fatal(f"Environment file for board '{self.name}' not found", file=str(file.absolute()))
        return file

    @property
    def is_bsim(self) -> bool:
        return "bsim" in self.name


@dataclass
class Project:
    name: str
    """Human readable name without any semantic meaning."""
    dir: Path
    """The directory where the project's CMakeLists.txt file is located."""
    upstream: bool
    """Whether this is a third-party (upstream) project or not."""


Args = list[str] | None


@dataclass
class Target(ABC):
    name: str
    """Human readable name without any semantic meaning."""
    parent_project: Project
    """The Project (i.e. the CMakeLists.txt file) that this target belongs to."""
    cmake_target: str
    """The name of the CMake target, as defined inside a CMakeLists.txt file somewhere."""
    build_subdir: str | None = None
    """Subdirectory INSIDE the build/ directory itself; i.e. for multi-target builds like sysbuild."""

    def post_build(self, cache: BuildCache) -> None:
        """Runs arbitrary optional steps after the target has been built.

        May be overridden if target requires a more complicated post-build process.
        """
        from gale.tasks import common_post_build_task  # noqa: PLC0415

        common_post_build_task(cache)

    def run(self, cache: BuildCache, *, gdb: bool, valgrind: bool, real_time: bool) -> None:
        """Implements running/debugging the target.

        May be overridden if target requires a more complicated run process.
        """
        from gale.tasks import common_run_task  # noqa: PLC0415

        common_run_task(cache, gdb=gdb, valgrind=valgrind, real_time=real_time)


class CMakeCache:
    """Interface around CmakeCache.txt."""

    def __init__(self, path: Path) -> None:
        self.path: Path = path
        self.values: dict[str, str | None] = {}
        line_pattern: re.Pattern[str] = re.compile(r"^([^\s:]+):\w*=(.*)$")

        with path.open() as file:
            for line in file:
                match: re.Match[str] | None = line_pattern.match(line.strip())
                if match:
                    key, value = match.groups()
                    self.values[key] = value if value else None

    def get(self, key: str) -> str:
        try:
            return str(self.values[key])
        except KeyError:
            log.fatal(f"CMakeCache {self.path} does not define {key}")

    @property
    def gdb(self) -> str:
        return self.get("CMAKE_GDB")

    @property
    def zephyr_base(self) -> str:
        return self.get("ZEPHYR_BASE")

    @property
    def exe_path(self) -> str:
        return self.get("BYPRODUCT_KERNEL_EXE_NAME")

    @property
    def elf_path(self) -> str:
        return self.get("BYPRODUCT_KERNEL_ELF_NAME")

    @property
    def bsim_out_path(self) -> str:
        return self.get("BSIM_OUT_PATH")


class BuildCache:
    """Stores generated values for a target, such as devicetree, kconfig or CMake values."""

    def __init__(self, board: Board, target: Target, build_dir: Path) -> None:
        self.board: Board = board
        """Board used for generating this cache."""
        self.target: Target = target
        """Target used for generating this cache."""
        self.triplet: str = f"{board.name}:{target.parent_project.name}:{target.name}"
        """Uniquely identifies the build configuration: <board>:<project>:<target>."""
        self.build_dir: Path = build_dir
        """Directory where the compile_commands.json and other build artifacts are stored."""

        if not self.build_dir.exists():
            log.fatal(
                f"Build directory for the target '{self.triplet}' does not exist",
                dir=build_dir,
                help="Run 'gale build' on the target first",
            )

        cmake_cache_file: Path = build_dir / "CMakeCache.txt"
        if not cmake_cache_file.exists():
            log.fatal(f"CMakeCache for the target '{self.triplet}' does not exist", file=cmake_cache_file)

        self.cmake_cache: CMakeCache = CMakeCache(cmake_cache_file)
        """Dictionary of values parsed from the CMakeCache.txt file."""

        log.dbg("CMakeCache parsed", cache=self.cmake_cache.values)
