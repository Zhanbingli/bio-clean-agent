import logging
from typing import Optional

from rich.logging import RichHandler


def get_logger(name: str = "bio_clean_agent", level: int = logging.INFO, rich: bool = True) -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    logger.setLevel(level)
    if rich:
        handler: logging.Handler = RichHandler(rich_tracebacks=True)
    else:
        handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger
