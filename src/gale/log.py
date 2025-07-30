import logging
import os
from functools import cache
from typing import Any, NoReturn

import structlog
from rich import pretty
from rich.box import HORIZONTALS, Box
from rich.console import Console, ConsoleRenderable
from rich.highlighter import ReprHighlighter
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table
from rich.text import Text
from rich.theme import Theme

from gale.common import is_verbose

_custom_log_themes = Theme(
    {
        "warning": "yellow",
        "error": "red",
        "critical": "red",
        "info": "green",
        "debug": "white",
        "code": "dim white",
    }
)

DETAILS_BOX: Box = Box(
    """
╭──╮\n
    \n
├──┤\n
    \n
├──┤\n
├──┤\n
    \n
╰──╯\n
""".replace("\n\n", "\n").strip()
)


def rule(
    width: int,
    tip_left: str = "╭",
    middle: str = "─",
    tip_right: str = "╮",
    style: str = "rule.line",
) -> Text:
    rule_text = tip_left + middle * (width - 2) + tip_right
    return Text(rule_text, style=style)


def _console_printer(
    _logger: structlog.types.WrappedLogger,
    _method_name: str,
    event_dict: structlog.types.EventDict,
) -> str:
    console = Console(theme=_custom_log_themes)
    console.begin_capture()
    level: str = event_dict["level"]
    match level:
        case "warning":
            lvl = "WARNING: "
        case "error":
            lvl = "ERROR: "
        case _:
            lvl = ""

    # Print out the primary event message; derive color from error level:
    fmt: str = f"[{level}][{event_dict['timestamp']}] {lvl}{event_dict['event']}[/]"
    console.print(fmt)

    # These values are already printed above, no need to duplicate them:
    for key in ["level", "timestamp", "event"]:
        if key in event_dict:
            event_dict.pop(key)

    # Print out event values as a custom table:
    # This is a custom table because we do not want padding of any kind before each row,
    # as such padding makes the values hard to copy from the CLI.
    if event_dict:
        for i, (key, value) in enumerate(event_dict.items()):
            if i == 0:
                console.print(rule(console.width, tip_left="╭", tip_right="╮", style=level))

            _key = key.replace("_", " ")
            text: str = f"[{level}] {_key}: [/][white]{value!s}[/]"
            console.print(text)

            if i == len(event_dict) - 1:
                console.print(rule(console.width, tip_left="╰", tip_right="╯", style=level))
            else:
                console.print(rule(console.width, tip_left="├", tip_right="┤", style=level))

    return console.end_capture().strip()


@cache
def get_logger() -> structlog.types.FilteringBoundLogger:
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.TimeStamper(fmt="%H:%M:%S", utc=False),
            _console_printer,
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.NOTSET),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=False,
    )
    return structlog.get_logger()


def dbg(msg: str, **kwargs: Any) -> None:  # noqa: ANN401
    if is_verbose():
        get_logger().debug(msg, **kwargs)


def inf(msg: str, **kwargs: Any) -> None:  # noqa: ANN401
    get_logger().info(msg, **kwargs)


def wrn(msg: str, **kwargs: Any) -> None:  # noqa: ANN401
    get_logger().warning(msg, **kwargs)


def err(msg: str, **kwargs: Any) -> None:  # noqa: ANN401
    get_logger().error(msg, **kwargs)


def fatal(msg: str, **kwargs: Any) -> NoReturn:  # noqa: ANN401
    err(msg, **kwargs)
    os._exit(-1)
