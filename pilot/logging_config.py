"""Debug logging configuration for pilot."""
import logging
import os
from pathlib import Path
from config import PILOT_HOME

# Log file path
LOG_FILE = PILOT_HOME / "logs" / "pilot.log"

# Configure logging based on DEBUG env var
DEBUG = os.getenv("PILOT_DEBUG", "").lower() in ("1", "true", "yes")

def setup_logging():
    """Set up logging configuration."""
    level = logging.DEBUG if DEBUG else logging.INFO

    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s [%(name)s] %(message)s",
        datefmt="%H:%M:%S"
    )

    # Console handler
    console = logging.StreamHandler()
    console.setLevel(level)
    console.setFormatter(formatter)

    # File handler (always debug level for file)
    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    # Root logger
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    root.addHandler(console)
    root.addHandler(file_handler)

    return logging.getLogger("pilot")

# Create logger on import
logger = setup_logging()
