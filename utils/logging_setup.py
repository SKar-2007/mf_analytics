import logging
import sys
from pathlib import Path
from typing import Optional

try:
    from config import config
except ImportError:
    config = None


def setup_logger(
    name: str = "bluestock",
    level: Optional[str] = None,
    log_file: Optional[str] = None,
) -> logging.Logger:
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    if level is None and config is not None:
        level = config.resolve("logging", "level") or "INFO"
    level = level or "INFO"
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    fmt = logging.Formatter(
        config.resolve("logging", "format")
        if config
        else "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s"
    )

    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(fmt)
    logger.addHandler(ch)

    if log_file is None and config is not None:
        log_path = config.resolve("logging", "file")
        if log_path:
            log_file = str(config.base_dir / log_path)

    if log_file:
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(log_file)
        fh.setFormatter(fmt)
        logger.addHandler(fh)

    return logger
