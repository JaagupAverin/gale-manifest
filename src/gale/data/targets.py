from enum import Enum
from pathlib import Path
from typing import override

from gale import log
from gale.data.projects import HMI_APP_PROJECT, SENSOR_APP_PROJECT
from gale.data.structs import BuildCache, Target
from gale.tasks import task_run_app_in_bsim


class RawTarget(Target):
    @override
    def pre_build(self, root_build_dir: Path) -> None:
        log.inf(f"No post-configure steps to execute for {self.name}")

    @override
    def post_build(self, cache: BuildCache) -> None:
        log.inf(f"No post-build steps to execute for {cache.triplet}")

    @override
    def run(self, cache: BuildCache, *, gdb: bool, real_time: bool) -> None:
        log.fatal(f"Target {self.name} does not implement running/debugging.")


class AppTarget(Target):
    """A simple application target that consists of a single executable that can be flashed/simulated/debugged/etc."""

    @override
    def pre_build(self, root_build_dir: Path) -> None:
        log.dbg(f"No pre-build steps to execute for {self.name}")

    @override
    def post_build(self, cache: BuildCache) -> None:
        log.dbg(f"No post-build steps to execute for {cache.triplet}")

    @override
    def run(self, cache: BuildCache, *, gdb: bool, real_time: bool) -> None:
        if cache.board.is_bsim:
            task_run_app_in_bsim(cache, gdb=gdb, real_time=real_time)
        else:
            log.fatal("Direct running on board not yet implemented.")


HMI_APP_TARGET = AppTarget(
    name="hmi_app",
    parent_project=HMI_APP_PROJECT,
    cmake_target="hmi_app",
    build_subdir="hmi_app",
)

SENSOR_APP_TARGET = AppTarget(
    name="sensor_app",
    parent_project=SENSOR_APP_PROJECT,
    cmake_target="sensor_app",
    build_subdir="sensor_app",
)


class TargetEnum(Enum):
    HMI_APP = "hmi_app"
    SENSOR_APP = "sensor_app"


TARGETS: dict[TargetEnum, Target] = {
    TargetEnum.HMI_APP: HMI_APP_TARGET,
    TargetEnum.SENSOR_APP: SENSOR_APP_TARGET,
}


def get_target(target: TargetEnum) -> Target:
    return TARGETS[target]
