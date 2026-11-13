"""Central logging configuration for SCOPE."""

from __future__ import annotations

import logging
import os
from typing import Optional


def setup_logging(level: Optional[str] = None) -> logging.Logger:
    """Configure root logging and return the SCOPE application logger.

    Args:
        level: Optional log level name (DEBUG, INFO, WARNING, ERROR).
            Defaults to ``SCOPE_LOG_LEVEL`` env var or INFO.

    Returns:
        Configured logger named ``scope``.
    """
    resolved = (level or os.getenv("SCOPE_LOG_LEVEL", "INFO")).upper()
    numeric = getattr(logging, resolved, logging.INFO)

    root = logging.getLogger()
    # Avoid force=True so pytest/caplog handlers are preserved when present.
    if not root.handlers:
        logging.basicConfig(
            level=numeric,
            format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    else:
        root.setLevel(numeric)

    logger = logging.getLogger("scope")
    logger.setLevel(numeric)
    logger.debug("Logging initialised at level %s", resolved)
    return logger
