from enum import Enum

from gale.data.projects import SHARED_PROJECT
from gale.data.structs import Board

NRF54L15_DK_BOARD = Board(
    name="nrf54l15dk",
    dir=SHARED_PROJECT.dir / "boards/nrf54l15dk",
)

NRF54L15_BSIM_BOARD = Board(
    name="nrf54l15bsim",
    dir=SHARED_PROJECT.dir / "boards/nrf54l15bsim",
)

NRF5340_BSIM_BOARD = Board(
    name="nrf5340bsim",
    dir=SHARED_PROJECT.dir / "boards/nrf5340bsim",
)


class BoardEnum(str, Enum):
    NRF54L15_DK = "nrf54l15dk"
    NRF54L15_BSIM = "nrf54l15bsim"
    NRF5340_BSIM = "nrf5340bsim"


BOARDS: dict[BoardEnum, Board] = {
    BoardEnum.NRF54L15_DK: NRF54L15_DK_BOARD,
    BoardEnum.NRF54L15_BSIM: NRF54L15_BSIM_BOARD,
    BoardEnum.NRF5340_BSIM: NRF5340_BSIM_BOARD,
}


def get_board(board: BoardEnum) -> Board:
    return BOARDS[board]
