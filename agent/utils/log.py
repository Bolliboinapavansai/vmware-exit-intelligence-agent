import logging

try:
    from rich.logging import RichHandler
    _HAS_RICH = True
except Exception:
    RichHandler = None
    _HAS_RICH = False


def setup_logging(level: str = "INFO") -> None:
    lvl = getattr(logging, level.upper(), logging.INFO)
    fmt = "%(asctime)s %(levelname)s %(name)s - %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"

    if _HAS_RICH:
        logging.basicConfig(
            level=lvl,
            format=fmt,
            datefmt=datefmt,
            handlers=[RichHandler(rich_tracebacks=True)],
        )
    else:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(fmt=fmt, datefmt=datefmt)
        handler.setFormatter(formatter)
        logging.basicConfig(level=lvl, handlers=[handler])


logger = logging.getLogger("vmxagent")
