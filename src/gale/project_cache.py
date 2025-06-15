import re
from pathlib import Path
from typing import override

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
    def native_executable(self) -> str:
        return self.get("BYPRODUCT_KERNEL_EXE_NAME")


class ProjectCache:
    """Stores generated values for a project, such as devicetree, kconfig or CMake values."""

    def __init__(self, build_dir: Path) -> None:
        self.build_dir: Path = build_dir

        if not self.build_dir.exists():
            log.fatal(f"Build directory {self.build_dir} does not exist")

        self.cmake_cache_file: Path = build_dir / "CMakeCache.txt"
        if not self.cmake_cache_file.exists():
            log.fatal(f"CMakeCache {self.cmake_cache_file} does not exist")
        self.cmake_cache: CMakeCache = CMakeCache(self.cmake_cache_file)
        log.dbg("CMakeCache parsed", cache=self.cmake_cache.values)
