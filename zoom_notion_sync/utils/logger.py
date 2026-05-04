"""utils/logger.py — Configures clean console + file logging."""

import logging
import os
from datetime import datetime

from config.settings import LOG_LEVEL


def setup_logger(name: str) -> logging.Logger:
    level = getattr(logging, LOG_LEVEL.upper(), logging.INFO)

    # Create logs directory
    os.makedirs("logs", exist_ok=True)
    log_file = f"logs/sync_{datetime.now().strftime('%Y%m%d')}.log"

    logging.basicConfig(
        level=level,
        format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
        datefmt="%H:%M:%S",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_file),
        ],
    )
    return logging.getLogger(name)
