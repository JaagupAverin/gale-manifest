from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from gale.util import get_manifest_dir, get_projects_dir


@dataclass
class Project:
    name: str
    path_getter: Callable[[], Path]
    upstream: bool

    @property
    def path(self) -> Path:
        """Returns path from path_getter.

        This indirection is needed because:
        1. Determining the full path may require invoking other CLI commands;
        2. These commands may be slow(ish);
        3. This tool should be fast(ish) due to live shell completion support;
        """
        return self.path_getter()


MANIFEST_PROJECT = Project(
    "manifest",
    lambda: get_manifest_dir(),
    upstream=False,
)

SENSOR_APP_PROJECT = Project(
    "sensor-app",
    lambda: get_projects_dir() / "sensor_app",
    upstream=False,
)

HMI_APP_PROJECT = Project(
    "hmi-app",
    lambda: get_projects_dir() / "hmi_app",
    upstream=False,
)

SHARED_PROJECT = Project(
    "shared",
    lambda: get_projects_dir() / "shared",
    upstream=False,
)

ZEPHYR_PROJECT = Project(
    "zephyr",
    lambda: get_projects_dir() / "zephyr",
    upstream=True,
)

PROJECTS: list[Project] = [
    MANIFEST_PROJECT,
    SENSOR_APP_PROJECT,
    HMI_APP_PROJECT,
    SHARED_PROJECT,
    ZEPHYR_PROJECT,
]


class ProjectEnum(str, Enum):
    HMI_APP = "hmi"
    SENSOR_APP = "sensor"


def get_project(project: ProjectEnum) -> Project:
    match project:
        case ProjectEnum.HMI_APP:
            return HMI_APP_PROJECT
        case ProjectEnum.SENSOR_APP:
            return SENSOR_APP_PROJECT
