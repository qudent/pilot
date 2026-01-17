"""Gemini Flash for fast command translation."""
import json
import base64
from google import genai
from google.genai import types
from config import GEMINI_API_KEY, GEMINI_MODEL

client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

SYSTEM_PROMPT = """You control a dev server via tmux. Respond in JSON only.

Input: user command (voice/text), current server state, context
Output: JSON with:
- "summary": 1-line status for user (what you're doing/found)
- "commands": list of {"target": "session:window", "keys": "command to run"} or []
- "task": updated task description if changed, else null
- "note": short log entry for activity log

Be fast and concise. Common patterns:
- "check X" → look at relevant tmux pane, summarize
- "run X" → send command to appropriate session
- "status" → summarize all sessions
- "start X" → create session if needed, run command

Respond ONLY with valid JSON, no markdown."""


async def translate(
    text: str = None,
    audio_b64: str = None,
    image_b64: str = None,
    state: dict = None,
    context: str = None,
    gps: dict = None,
) -> dict:
    """Translate multimodal input to commands."""
    if not client:
        return {
            "summary": "Error: GEMINI_API_KEY not set",
            "commands": [],
            "task": None,
            "note": "missing API key"
        }

    # Build content parts
    parts = []

    # Add context
    user_msg = f"Server state:\n```json\n{json.dumps(state, indent=2)}\n```\n\n"
    if context:
        user_msg += f"Context:\n{context[:1000]}\n\n"
    if gps:
        user_msg += f"Location: {gps}\n\n"

    user_msg += "User command: "

    if text:
        user_msg += text
    else:
        user_msg += "(see audio/image)"

    parts.append(types.Part.from_text(user_msg))

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
        response = await client.aio.models.generate_content(
            model=GEMINI_MODEL,
            contents=[types.Content(role="user", parts=parts)],
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.1,  # Low for consistency
                max_output_tokens=500,  # Keep responses short
            )
        )

        # Parse JSON response
        text_response = response.text.strip()
        # Handle markdown code blocks
        if text_response.startswith("```"):
            text_response = text_response.split("```")[1]
            if text_response.startswith("json"):
                text_response = text_response[4:]

        return json.loads(text_response)

    except json.JSONDecodeError as e:
        return {
            "summary": f"Parse error: {response.text[:100]}",
            "commands": [],
            "task": None,
            "note": f"JSON parse failed: {e}"
        }
    except Exception as e:
        return {
            "summary": f"Error: {str(e)[:50]}",
            "commands": [],
            "task": None,
            "note": f"gemini error: {e}"
        }
