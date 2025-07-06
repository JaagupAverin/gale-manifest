from enum import Enum
from typing import override

from gale import log
from gale.data.projects import HMI_APP_PROJECT, SENSOR_APP_PROJECT
from gale.data.structs import BuildCache, Target
from gale.tasks import common_post_build_task, common_run_task


class RawTarget(Target):
    @override
    def post_build(self, cache: BuildCache) -> None:
        log.inf(f"No post-build steps to execute for {cache.triplet}")

    @override
    def run(self, cache: BuildCache, *, gdb: bool, real_time: bool) -> None:
        log.fatal(f"Target {self.name} does not implement running/debugging.")


class AppTarget(Target):
    """A simple application target that consists of a single executable that can be flashed/simulated/debugged/etc."""

    @override
    def post_build(self, cache: BuildCache) -> None:
        common_post_build_task(cache)

    @override
    def run(self, cache: BuildCache, *, gdb: bool, real_time: bool) -> None:
        common_run_task(cache, gdb=gdb, real_time=real_time)


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
