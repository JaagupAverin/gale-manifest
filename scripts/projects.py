from dataclasses import dataclass, field
from enum import Enum

from util import WEST_TOPDIR


class ProjectType(Enum):
    App = "app"
    Dependency = "dependency"
    Manifest = "manifest"


@dataclass
class Project:
    name: str
    path: str
    type: ProjectType
    is_fork: bool = field(default=False)

    def __post_init__(self) -> None:
        self.path = f"{WEST_TOPDIR}/{self.path}"


PROJECTS: list[Project] = [
    Project(
        "manifest",
        "manifest",
        ProjectType.Manifest,
    ),
    Project(
        "sensor-app",
        "sensor_app",
        ProjectType.App,
    ),
    Project(
        "hmi-app",
        "hmi_app",
        ProjectType.App,
    ),
    Project(
        "shared",
        "shared",
        ProjectType.Dependency,
    ),
    Project(
        "zephyr",
        "zephyr",
        ProjectType.Dependency,
        is_fork=True,
    ),
    Project(
        "hal_espressif",
        "modules/hal/espressif",
        ProjectType.Dependency,
        is_fork=True,
    ),
]
