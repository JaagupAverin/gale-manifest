from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from gale.util import get_manifest_dir, get_projects_dir


class ProjectType(Enum):
    App = "app"
    Dependency = "dependency"
    Manifest = "manifest"


@dataclass
class Project:
    name: str
    path_getter: Callable[[], Path]
    type: ProjectType
    is_fork: bool = field(default=False)

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
    ProjectType.Manifest,
)

SENSOR_APP_PROJECT = Project(
    "sensor-app",
    lambda: get_projects_dir() / "sensor_app",
    ProjectType.App,
)

HMI_APP_PROJECT = Project(
    "hmi-app",
    lambda: get_projects_dir() / "hmi_app",
    ProjectType.App,
)

SHARED_PROJECT = Project(
    "shared",
    lambda: get_projects_dir() / "shared",
    ProjectType.Dependency,
)

PROJECTS: list[Project] = [
    MANIFEST_PROJECT,
    SENSOR_APP_PROJECT,
    HMI_APP_PROJECT,
    SHARED_PROJECT,
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
