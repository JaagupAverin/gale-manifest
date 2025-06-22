import re
from pathlib import Path

from gale import log


class CMakeCache:
    """Interface around CmakeCache.txt."""

    def __init__(self, path: Path) -> None:
        self.path: Path = path
        self.values: dict[str, str | None] = {}
        line_pattern = re.compile(r"^([^\s:]+):\w*=(.*)$")

        with path.open() as file:
            for line in file:
                match = line_pattern.match(line.strip())
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


class BuildCache:
    """Stores generated values for a target, such as devicetree, kconfig or CMake values."""

    def __init__(self, triplet: str, build_dir: Path) -> None:
        self.triplet: str = triplet
        """Uniquely identifies the build configuration: <project>:<board>:<target>."""
        self.build_dir: Path = build_dir
        """Directory where the compile_commands.json and other build artifacts are stored."""

        if not self.build_dir.exists():
            log.fatal(
                f"Build directory for the target '{triplet}' does not exist",
                dir=build_dir,
                help="Run 'gale build' on the target first",
            )

        cmake_cache_file: Path = build_dir / "CMakeCache.txt"
        if not cmake_cache_file.exists():
            log.fatal(f"CMakeCache for the target '{triplet}' does not exist", file=cmake_cache_file)
        self.cmake_cache: CMakeCache = CMakeCache(cmake_cache_file)
        """Dictionary of values parsed from the CMakeCache.txt file."""

        log.dbg("CMakeCache parsed", cache=self.cmake_cache.values)
