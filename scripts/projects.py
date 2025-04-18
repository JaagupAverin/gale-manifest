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


MANIFEST_PROJECT = Project(
    "manifest",
    "manifest",
    ProjectType.Manifest,
)

SENSOR_APP_PROJECT = Project(
    "sensor-app",
    "sensor_app",
    ProjectType.App,
)

HMI_APP_PROJECT = Project(
    "hmi-app",
    "hmi_app",
    ProjectType.App,
)

SHARED_PROJECT = Project(
    "shared",
    "shared",
    ProjectType.Dependency,
)

ZEPHYR_PROJECT = Project(
    "zephyr",
    "zephyr",
    ProjectType.Dependency,
    is_fork=True,
)

HAL_ESPRESSIF_PROJECT = Project(
    "hal_espressif",
    "modules/hal/espressif",
    ProjectType.Dependency,
    is_fork=True,
)

PROJECTS: list[Project] = [
    MANIFEST_PROJECT,
    SENSOR_APP_PROJECT,
    HMI_APP_PROJECT,
    SHARED_PROJECT,
    ZEPHYR_PROJECT,
    HAL_ESPRESSIF_PROJECT,
]
