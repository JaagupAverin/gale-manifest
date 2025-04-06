from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from functools import cache


@cache
def get_manifest_dir() -> str:
    from gale.util import get_west_topdir

    return f"{get_west_topdir()}/gale"


@cache
def get_projects_dir() -> str:
    return f"{get_manifest_dir()}/projects"


class ProjectType(Enum):
    App = "app"
    Dependency = "dependency"
    Manifest = "manifest"


@dataclass
class Project:
    name: str
    path_getter: Callable[[], str]
    type: ProjectType
    is_fork: bool = field(default=False)

    @property
    def path(self) -> str:
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
    lambda: f"{get_projects_dir()}/sensor_app",
    ProjectType.App,
)

HMI_APP_PROJECT = Project(
    "hmi-app",
    lambda: f"{get_projects_dir()}/hmi_app",
    ProjectType.App,
)

SHARED_PROJECT = Project(
    "shared",
    lambda: f"{get_projects_dir()}/shared",
    ProjectType.Dependency,
)

ZEPHYR_PROJECT = Project(
    "zephyr",
    lambda: f"{get_projects_dir()}/zephyr",
    ProjectType.Dependency,
    is_fork=True,
)

HAL_ESPRESSIF_PROJECT = Project(
    "hal_espressif",
    lambda: f"{get_projects_dir()}/modules/hal/espressif",
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
