from dataclasses import dataclass
from enum import Enum

from gale.data.projects import HMI_APP_PROJECT, SENSOR_APP_PROJECT, Project


@dataclass
class Target:
    name: str
    parent_project: Project
    cmake_target: str
    build_subdir: str | None


HMI_APP_TARGET = Target(
    name="hmi_app",
    parent_project=HMI_APP_PROJECT,
    cmake_target="hmi_app",
    build_subdir="hmi_app",
)

SENSOR_APP_TARGET = Target(
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
