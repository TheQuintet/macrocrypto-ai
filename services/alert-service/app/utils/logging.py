"""Logging configuration for alert-service"""

import logging
import sys
from typing import Optional

from app.config import settings


def setup_logging(level: Optional[str] = None) -> None:
    """
    Setup logging configuration for the application.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
               Defaults to settings.LOG_LEVEL
    """
    log_level = level or settings.LOG_LEVEL
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
        force=True,
    )
    
    # Set log levels for third-party libraries
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("pika").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
    logging.getLogger("apscheduler").setLevel(logging.WARNING)
    
    # Create logger for this module
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured at {log_level} level")


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name."""
    return logging.getLogger(name)