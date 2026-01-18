import os
import secrets
from pathlib import Path

# Directories
PILOT_HOME = Path.home() / ".pilot"
PILOT_HOME.mkdir(exist_ok=True)
(PILOT_HOME / "logs").mkdir(exist_ok=True)

# Auth token - generate once, store in file
TOKEN_FILE = PILOT_HOME / "token"
if TOKEN_FILE.exists():
    AUTH_TOKEN = TOKEN_FILE.read_text().strip()
else:
    AUTH_TOKEN = secrets.token_urlsafe(32)
    TOKEN_FILE.write_text(AUTH_TOKEN)
    TOKEN_FILE.chmod(0o600)

# Files
CONTEXT_FILE = PILOT_HOME / "context.md"
PROMPT_FILE = PILOT_HOME / "prompt.md"

# Server
HOST = "127.0.0.1"  # Caddy will proxy
PORT = int(os.getenv("PILOT_PORT", "7777"))

# Gemini - using flash for speed
GEMINI_MODEL = "gemini-2.0-flash-exp"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

# Context limits (lines)
CONTEXT_MAX_LINES = 60


def load_user_instructions() -> str:
    """Load user-defined instructions from ~/.pilot/prompt.md if it exists.

    Returns the file contents if the file exists, otherwise returns None
    which signals to use default instructions.
    """
    if PROMPT_FILE.exists():
        return PROMPT_FILE.read_text().strip()
    return None
