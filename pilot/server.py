"""Pilot server - WebSocket for low-latency control."""
import asyncio
import json
import time
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from pathlib import Path

import config
import tmux
import context
import gemini

app = FastAPI(title="Pilot")

# Serve static files (web client)
STATIC_DIR = Path(__file__).parent / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


def verify_token(token: str) -> bool:
    """Check auth token."""
    return token == config.AUTH_TOKEN


@app.get("/")
async def index():
    """Serve web client."""
    client_file = STATIC_DIR / "index.html"
    if client_file.exists():
        return HTMLResponse(client_file.read_text())
    return HTMLResponse("<h1>Pilot</h1><p>Web client not found. Use WebSocket at /ws</p>")


@app.get("/token")
async def get_token():
    """Show token (for initial setup only - access from server)."""
    return {"token": config.AUTH_TOKEN, "note": "Save this in your client"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = Query(None)):
    """Main WebSocket endpoint for commands."""

    # Auth check
    if not token or not verify_token(token):
        await websocket.close(code=4001, reason="Invalid token")
        return

    await websocket.accept()

    # Send initial state
    state = tmux.get_state()
    ctx = context.load() or context.init()
    await websocket.send_json({
        "type": "state",
        "state": state,
        "context": ctx
    })

    try:
        while True:
            # Receive command
            data = await websocket.receive_json()
            start = time.time()

            msg_type = data.get("type", "cmd")

            if msg_type == "ping":
                await websocket.send_json({"type": "pong", "ts": time.time()})
                continue

            if msg_type == "cmd":
                # Get current state
                state = tmux.get_state()
                ctx = context.load()

                # Translate with Gemini
                result = await gemini.translate(
                    text=data.get("text"),
                    audio_b64=data.get("audio"),
                    image_b64=data.get("image"),
                    state=state,
                    context=ctx,
                    gps=data.get("gps"),
                )

                # Send immediate response (before executing commands)
                elapsed = int((time.time() - start) * 1000)
                await websocket.send_json({
                    "type": "response",
                    "summary": result.get("summary", ""),
                    "latency_ms": elapsed,
                })

                # Execute commands
                for cmd in result.get("commands", []):
                    target = cmd.get("target", "")
                    keys = cmd.get("keys", "")
                    if keys:
                        session = target.split(":")[0] if target else None
                        window = target.split(":")[1] if ":" in target else None
                        tmux.send_keys(keys, session=session, window=window)

                # Update context
                context.update(
                    task=result.get("task"),
                    note=result.get("note"),
                    state=state,
                )

                # Send updated state
                await asyncio.sleep(0.5)  # Let commands run
                new_state = tmux.get_state()
                await websocket.send_json({
                    "type": "state",
                    "state": new_state,
                })

    except WebSocketDisconnect:
        pass
    except Exception as e:
        await websocket.send_json({"type": "error", "message": str(e)})


# HTTP fallback for simple commands
@app.post("/cmd")
async def http_command(
    text: str = None,
    token: str = Query(None),
):
    """HTTP endpoint for simple text commands."""
    if not token or not verify_token(token):
        raise HTTPException(status_code=401, detail="Invalid token")

    state = tmux.get_state()
    ctx = context.load()

    result = await gemini.translate(text=text, state=state, context=ctx)

    # Execute commands
    for cmd in result.get("commands", []):
        target = cmd.get("target", "")
        keys = cmd.get("keys", "")
        if keys:
            session = target.split(":")[0] if target else None
            tmux.send_keys(keys, session=session)

    context.update(task=result.get("task"), note=result.get("note"), state=state)

    return result


if __name__ == "__main__":
    import uvicorn
    print(f"Starting Pilot on {config.HOST}:{config.PORT}")
    print(f"Token: {config.AUTH_TOKEN}")
    uvicorn.run(app, host=config.HOST, port=config.PORT)
