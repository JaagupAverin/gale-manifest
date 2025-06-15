from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from gale import log
from gale.projects import SHARED_PROJECT


@dataclass
class Board:
    name: str
    dir_getter: Callable[[], Path]

    @property
    def env(self) -> Path:
        file = self.dir_getter() / "environment"
        if not file.exists():
            log.fatal(f"Environment file for board '{self.name}' not found", file=str(file.absolute()))
        return file

    @property
    def is_bsim(self) -> bool:
        return "bsim" in self.name


NRF54L15_DK_BOARD = Board(
    "nrf54l15dk",
    lambda: SHARED_PROJECT.path / "boards/nrf54l15dk",
)

NRF54L15_BSIM_BOARD = Board(
    "nrf54l15bsim",
    lambda: SHARED_PROJECT.path / "boards/nrf54l15bsim",
)

BOARDS: list[Board] = [
    NRF54L15_DK_BOARD,
    NRF54L15_BSIM_BOARD,
]


class BoardEnum(str, Enum):
    NRF54L15_DK = "nrf54l15dk"
    NRF54L15_BSIM = "nrf54l15bsim"


def get_board(board_name: BoardEnum) -> Board:
    match board_name:
        case BoardEnum.NRF54L15_DK:
            return NRF54L15_DK_BOARD
        case BoardEnum.NRF54L15_BSIM:
            return NRF54L15_BSIM_BOARD
