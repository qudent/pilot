"""Gemini Flash for command translation and display generation."""
import base64
import logging
from pydantic import BaseModel, Field
from typing import Optional
from google import genai
from google.genai import types
from config import GEMINI_API_KEY, GEMINI_MODEL, load_user_instructions


class TmuxCommand(BaseModel):
    """A tmux command to execute."""
    target: str = Field(default="", description="tmux target like 'session:window'")
    keys: str = Field(default="", description="keys/command to send")


class PilotResponse(BaseModel):
    """Structured response from Gemini for pilot actions."""
    commands: list[TmuxCommand] = Field(default_factory=list, description="tmux commands to execute")
    display: str = Field(description="plain text status to show user")
    task: Optional[str] = Field(default=None, description="current task description")
    note: Optional[str] = Field(default=None, description="short activity log entry")

logger = logging.getLogger("pilot.gemini")

client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

# Core instruction for the schema - minimal since structure is enforced by response_schema
CORE_SCHEMA_INSTRUCTION = """You control a dev server via tmux. Given user input and tmux screen contents:

1. Return tmux commands to execute (or empty list if just viewing)
2. Generate a plain text status display for the user's screen

The display should fit the user's screen dimensions (cols/rows given) and be concise, terminal-style."""

# Default user instructions - can be customized via ~/.pilot/prompt.md
DEFAULT_USER_INSTRUCTIONS = """Style preferences:
- Be concise and direct
- Use terminal-style output, no emojis or fluff
- Summarize what's happening across tmux sessions
- Include relevant output snippets when useful

Common patterns:
- "status" or "what's happening" -> summarize all sessions
- "run X" -> send command to appropriate session
- "check Y" -> look at session Y and report

Keep display text sized for the screen dimensions provided."""


def get_system_prompt() -> str:
    """Build the system prompt from core instruction and user instructions."""
    user_instructions = load_user_instructions() or DEFAULT_USER_INSTRUCTIONS
    return f"{CORE_SCHEMA_INSTRUCTION}\n\n{user_instructions}"


async def translate(
    text: str = None,
    audio_b64: str = None,
    image_b64: str = None,
    screen: dict = None,
    tmux_screens: dict = None,
    context: str = None,
    gps: dict = None,
) -> dict:
    """Translate input to commands and generate display."""
    if not client:
        return {
            "commands": [],
            "display": "Error: GEMINI_API_KEY not set",
            "task": None,
            "note": "missing API key"
        }

    # Build prompt
    screen = screen or {"cols": 80, "rows": 24}
    prompt = f"Screen: {screen['cols']}x{screen['rows']} chars\n\n"

    if tmux_screens:
        prompt += "=== TMUX SESSIONS ===\n"
        for name, content in tmux_screens.items():
            prompt += f"\n[{name}]\n{content}\n"
        prompt += "\n"

    if context:
        prompt += f"=== CONTEXT ===\n{context[:500]}\n\n"

    if gps:
        prompt += f"Location: {gps['lat']:.4f}, {gps['lon']:.4f}\n\n"

    prompt += f"User: {text or '(voice/image input)'}"

    parts = [types.Part.from_text(text=prompt)]

    # Add audio if present
    if audio_b64:
        parts.append(types.Part.from_bytes(
            data=base64.b64decode(audio_b64),
            mime_type="audio/webm"
        ))

    # Add image if present
    if image_b64:
        parts.append(types.Part.from_bytes(
            data=base64.b64decode(image_b64),
            mime_type="image/jpeg"
        ))

    try:
        logger.debug(f"Prompt length: {len(prompt)} chars")
        response = await client.aio.models.generate_content(
            model=GEMINI_MODEL,
            contents=[types.Content(role="user", parts=parts)],
            config=types.GenerateContentConfig(
                system_instruction=get_system_prompt(),
                temperature=0.1,
                max_output_tokens=1000,
                response_mime_type="application/json",
                response_schema=PilotResponse,
            )
        )

        # Parse with Pydantic for validation
        result = PilotResponse.model_validate_json(response.text).model_dump()
        logger.debug(f"Parsed: {len(result.get('commands', []))} commands")
        return result

    except Exception as e:
        logger.error(f"Gemini error: {e}", exc_info=True)
        return {
            "commands": [],
            "display": f"Error: {str(e)[:100]}",
            "task": None,
            "note": f"error: {e}"
        }
