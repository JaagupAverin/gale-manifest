from enum import Enum

from gale.data.structs import Board

NRF54L15_DK_BOARD = Board(
    name="nrf54l15dk",
    primary_board="nrf54l15dk/nrf54l15/cpuapp",
)

NRF54L15_BSIM_BOARD = Board(
    name="nrf54l15bsim",
    primary_board="nrf54l15bsim/nrf54l15/cpuapp",
)

NRF5340_BSIM_BOARD = Board(
    name="nrf5340bsim",
    primary_board="nrf5340bsim/nrf5340/cpuapp",
)


class BoardEnum(str, Enum):
    NRF54L15_DK = NRF54L15_DK_BOARD.name
    NRF54L15_BSIM = NRF54L15_BSIM_BOARD.name
    NRF5340_BSIM = NRF5340_BSIM_BOARD.name


BOARDS: dict[BoardEnum, Board] = {
    BoardEnum.NRF54L15_DK: NRF54L15_DK_BOARD,
    BoardEnum.NRF54L15_BSIM: NRF54L15_BSIM_BOARD,
    BoardEnum.NRF5340_BSIM: NRF5340_BSIM_BOARD,
}


def get_board(board: BoardEnum) -> Board:
    return BOARDS[board]
