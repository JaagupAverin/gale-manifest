from typing import Annotated

import typer
from serial.tools.list_ports import comports

from gale.data.boards import BoardEnum
from gale.data.projects import ProjectEnum
from gale.data.targets import TargetEnum

ProjectArg = Annotated[
    ProjectEnum,
    typer.Option(
        help="Target project: determines which CMakeLists.txt to use.",
        show_default=False,
    ),
]

BoardArg = Annotated[
    BoardEnum,
    typer.Option(
        help=(
            "Target board: determines which board's environment file to use. "
            "The environment file in turn defines the overlays, KConfigs, "
            "and other key variables used by the build system."
        ),
        show_default=False,
    ),
]

TargetArg = Annotated[
    TargetEnum,
    typer.Option(
        help=(
            "Target: determines which CMake target to build/run/debug. "
            "The CMake project that this target belongs to is determined automatically "
            "based on hardcoded relationships. If the desired target is not listed here, "
            "then it may be built manually using the 'cmake' command."
        ),
        show_default=False,
    ),
]

RebuildArg = Annotated[
    bool,
    typer.Option(
        help=(
            "Rebuild the target before running/debugging. "
            "Any extra build args from the latest build will be applied again "
            "(build args are automatically cached to disk and reused)."
        ),
        show_default=False,
    ),
]

ExtraBuildArgs = Annotated[
    list[str] | None,
    typer.Argument(
        help="Extra arguments to pass to the underlying build command, e.g. to 'west build'.",
        show_default=False,
    ),
]

ExtraRunArgs = Annotated[
    list[str] | None,
    typer.Argument(
        help="Extra arguments to pass to the underlying runner, e.g. to the BabbleSim executable.",
        show_default=False,
    ),
]


def _available_ports(incomplete: str) -> list[str]:
    ports: list[str] = [port.device for port in comports()]
    return [p for p in ports if p.startswith(incomplete)]


PortArg = Annotated[
    str,
    typer.Option(
        help="Serial port for communication, e.g. /dev/ttyUSB0",
        autocompletion=_available_ports,
        show_default=False,
    ),
]


def _common_baudrates(incomplete: str) -> list[str]:
    bauds: list[str] = ["9600", "115200", "250000"]
    return [b for b in bauds if b.startswith(incomplete)]


BaudrateArg = Annotated[
    int,
    typer.Option(
        help="Baud rate for serial communication.",
        autocompletion=_common_baudrates,
        show_default=True,
    ),
]
