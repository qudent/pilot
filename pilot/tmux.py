"""tmux session control."""
import subprocess
import json

def run(cmd: str) -> str:
    """Run shell command, return output."""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=5
        )
        return result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return "[timeout]"
    except Exception as e:
        return f"[error: {e}]"


def list_sessions() -> list[dict]:
    """List tmux sessions with their windows."""
    out = run("tmux list-sessions -F '#{session_name}' 2>/dev/null")
    if not out.strip() or "no server" in out:
        return []

    sessions = []
    for name in out.strip().split('\n'):
        if not name:
            continue
        windows = run(f"tmux list-windows -t {name} -F '#{{window_index}}:#{{window_name}}' 2>/dev/null")
        sessions.append({
            "name": name,
            "windows": windows.strip().split('\n') if windows.strip() else []
        })
    return sessions


def get_pane_content(session: str = None, lines: int = 30) -> str:
    """Get recent content from active pane."""
    target = f"-t {session}" if session else ""
    return run(f"tmux capture-pane {target} -p -S -{lines} 2>/dev/null")


def send_keys(keys: str, session: str = None, window: str = None) -> str:
    """Send keys to tmux pane."""
    target = ""
    if session:
        target = f"-t {session}"
        if window:
            target = f"-t {session}:{window}"

    # Escape for shell
    escaped = keys.replace("'", "'\\''")
    result = run(f"tmux send-keys {target} '{escaped}' Enter 2>/dev/null")
    return result or "sent"


def get_state() -> dict:
    """Get full tmux state for context."""
    sessions = list_sessions()
    state = {"sessions": sessions, "panes": {}}

    for sess in sessions:
        content = get_pane_content(sess["name"], lines=15)
        state["panes"][sess["name"]] = content[-500:] if content else ""  # Last 500 chars

    return state
