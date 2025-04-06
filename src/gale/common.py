_verbose: bool = False


def is_verbose() -> bool:
    return _verbose


def set_verbose(verbose: bool) -> None:
    global _verbose  # noqa: PLW0603
    _verbose = verbose
