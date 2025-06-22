from enum import Enum

from gale.data.paths import GALE_ROOT_DIR, PROJECTS_DIR
from gale.data.structs import Project

MANIFEST_PROJECT = Project(
    name="manifest",
    dir=GALE_ROOT_DIR,
    upstream=False,
)

SENSOR_APP_PROJECT = Project(
    name="sensor-app",
    dir=PROJECTS_DIR / "sensor_app",
    upstream=False,
)

HMI_APP_PROJECT = Project(
    name="hmi-app",
    dir=PROJECTS_DIR / "hmi_app",
    upstream=False,
)

SHARED_PROJECT = Project(
    name="shared",
    dir=PROJECTS_DIR / "shared",
    upstream=False,
)

ZEPHYR_PROJECT = Project(
    name="zephyr",
    dir=PROJECTS_DIR / "zephyr",
    upstream=True,
)


class ProjectEnum(str, Enum):
    MANIFEST = "manifest"
    HMI_APP = "hmi_app"
    SENSOR_APP = "sensor_app"
    SHARED = "shared"
    ZEPHYR = "zephyr"


PROJECTS: dict[ProjectEnum, Project] = {
    ProjectEnum.MANIFEST: MANIFEST_PROJECT,
    ProjectEnum.SENSOR_APP: SENSOR_APP_PROJECT,
    ProjectEnum.HMI_APP: HMI_APP_PROJECT,
    ProjectEnum.SHARED: SHARED_PROJECT,
    ProjectEnum.ZEPHYR: ZEPHYR_PROJECT,
}


def get_project(project: ProjectEnum) -> Project:
    return PROJECTS[project]
