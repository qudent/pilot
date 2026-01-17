"""Pilot server - WebSocket for low-latency control."""
import asyncio
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pathlib import Path

import config
import tmux
import context
import gemini

app = FastAPI(title="Pilot")

STATIC_DIR = Path(__file__).parent / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


def verify_token(token: str) -> bool:
    return token == config.AUTH_TOKEN


@app.get("/")
async def index():
    client_file = STATIC_DIR / "index.html"
    if client_file.exists():
        return HTMLResponse(client_file.read_text())
    return HTMLResponse("<h1>Pilot</h1>")


@app.get("/token")
async def get_token():
    return {"token": config.AUTH_TOKEN}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = Query(None)):
    if not token or not verify_token(token):
        await websocket.close(code=4001, reason="Invalid token")
        return

    await websocket.accept()

    try:
        while True:
            data = await websocket.receive_json()

            if data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
                continue

            if data.get("type") == "cmd":
                # Get full tmux screen contents
                screens = tmux.get_all_screens(lines=100)
                ctx = context.load()

                # Translate with Gemini
                result = await gemini.translate(
                    text=data.get("text"),
                    audio_b64=data.get("audio"),
                    image_b64=data.get("image"),
                    screen=data.get("screen"),
                    tmux_screens=screens,
                    context=ctx,
                    gps=data.get("gps"),
                )

                # Send display immediately
                await websocket.send_json({
                    "type": "display",
                    "text": result.get("display", ""),
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
                )

    except WebSocketDisconnect:
        pass
    except Exception as e:
        await websocket.send_json({"type": "error", "message": str(e)})


if __name__ == "__main__":
    import uvicorn
    print(f"Pilot on {config.HOST}:{config.PORT}")
    uvicorn.run(app, host=config.HOST, port=config.PORT)
