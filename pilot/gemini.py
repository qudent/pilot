"""Gemini Flash for command translation and display generation."""
import json
import base64
import logging
from google import genai
from google.genai import types
from config import GEMINI_API_KEY, GEMINI_MODEL

logger = logging.getLogger("pilot.gemini")

client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

SYSTEM_PROMPT = """You control a dev server. Given user input and tmux screen contents, do TWO things:

1. ACTIONS: Return commands to execute (or empty if just viewing)
2. DISPLAY: Generate a plain text status update for the user's screen

The display should:
- Fit the user's screen (cols/rows given)
- Summarize what's happening across tmux sessions
- Be concise, terminal-style, no fluff
- Include relevant output snippets if useful

Respond with JSON:
{
  "commands": [{"target": "session:window", "keys": "command"}],
  "display": "plain text status to show user",
  "task": "current task description or null",
  "note": "short activity log entry"
}

Keep display text sized for the screen dimensions provided."""


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
                system_instruction=SYSTEM_PROMPT,
                temperature=0.1,
                max_output_tokens=1000,
            )
        )

        text_response = response.text.strip()
        logger.debug(f"Response length: {len(text_response)} chars")

        # Strip markdown code blocks
        if text_response.startswith("```"):
            lines = text_response.split('\n')
            text_response = '\n'.join(lines[1:-1] if lines[-1] == '```' else lines[1:])

        result = json.loads(text_response)
        logger.debug(f"Parsed: {len(result.get('commands', []))} commands")
        return result

    except json.JSONDecodeError as e:
        logger.warning(f"JSON parse failed: {e}")
        logger.debug(f"Raw response: {response.text[:200] if response else 'None'}")
        return {
            "commands": [],
            "display": response.text[:500] if response else "Parse error",
            "task": None,
            "note": "json parse failed"
        }
    except Exception as e:
        logger.error(f"Gemini error: {e}", exc_info=True)
        return {
            "commands": [],
            "display": f"Error: {str(e)[:100]}",
            "task": None,
            "note": f"error: {e}"
        }
