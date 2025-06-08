import logging
import sys
from functools import cache
from typing import Any, NoReturn

import structlog
from rich import box, pretty
from rich.box import Box
from rich.console import Console, ConsoleRenderable
from rich.highlighter import ReprHighlighter
from rich.table import Table
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
    "╭──╮\n"  # /
    "│  │\n"  # /
    "├──┤\n"  # /
    "│  │\n"  # /
    "├──┤\n"  # /
    "├──┤\n"  # /
    "│  │\n"  # /
    "╰──╯\n"  # /
)


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

    # Format event dictionary into a Rich Table:
    if event_dict:
        table = Table(box=DETAILS_BOX, border_style=level, show_header=False, show_lines=True, expand=False)
        table.add_column("name", justify="right", style=level, max_width=10)
        for key, value in event_dict.items():
            key_text = key.replace("_", " ")

            if isinstance(value, dict):
                prettified_value = pretty.Pretty(
                    value,
                    highlighter=ReprHighlighter(),
                    indent_guides=False,
                    expand_all=True,
                )
            elif isinstance(value, ConsoleRenderable):
                prettified_value = value
            else:
                prettified_value = str(value).strip()
            table.add_row(key_text, prettified_value)

        console.print(table)
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
    sys.exit(-1)
