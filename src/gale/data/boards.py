from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from gale import log
from gale.data.projects import SHARED_PROJECT


@dataclass
class Board:
    name: str
    dir: Path

    @property
    def env(self) -> Path:
        file = self.dir / "environment"
        if not file.exists():
            log.fatal(f"Environment file for board '{self.name}' not found", file=str(file.absolute()))
        return file

    @property
    def is_bsim(self) -> bool:
        return "bsim" in self.name


NRF54L15_DK_BOARD = Board(
    name="nrf54l15dk",
    dir=SHARED_PROJECT.dir / "boards/nrf54l15dk",
)

NRF54L15_BSIM_BOARD = Board(
    name="nrf54l15bsim",
    dir=SHARED_PROJECT.dir / "boards/nrf54l15bsim",
)


class BoardEnum(str, Enum):
    NRF54L15_DK = "nrf54l15dk"
    NRF54L15_BSIM = "nrf54l15bsim"


BOARDS: dict[BoardEnum, Board] = {
    BoardEnum.NRF54L15_DK: NRF54L15_DK_BOARD,
    BoardEnum.NRF54L15_BSIM: NRF54L15_BSIM_BOARD,
}


def get_board(board: BoardEnum) -> Board:
    return BOARDS[board]
