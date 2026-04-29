"""
Shared logging setup for the AI Game Coach system.
Logs go to both the console and app.log in the project root.
"""

import logging
import os

_LOG_FILE = os.path.join(os.path.dirname(__file__), "app.log")
_configured = False


def get_logger(name: str) -> logging.Logger:
    """Return a configured logger for the given module name."""
    global _configured
    if not _configured:
        fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        logging.basicConfig(
            level=logging.INFO,
            format=fmt,
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler(_LOG_FILE, encoding="utf-8"),
            ],
        )
        _configured = True
    return logging.getLogger(name)
