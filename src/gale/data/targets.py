from __future__ import annotations

from enum import Enum

from gale.data.projects import HMI_APP_PROJECT, SENSOR_APP_PROJECT
from gale.data.structs import Target
from gale.tasks import common_debug_task, common_post_build_task, common_run_task

HMI_APP_TARGET = Target(
    name="hmi_app",
    parent_project=HMI_APP_PROJECT,
    cmake_target="hmi_app",
    build_subdir="hmi_app",
    post_build_handler=common_post_build_task,
    run_handler=common_run_task,
    debug_handler=common_debug_task,
)

SENSOR_APP_TARGET = Target(
    name="sensor_app",
    parent_project=SENSOR_APP_PROJECT,
    cmake_target="sensor_app",
    build_subdir="sensor_app",
    post_build_handler=common_post_build_task,
    run_handler=common_run_task,
    debug_handler=common_debug_task,
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
