"""tmux session control with full screen capture."""
import subprocess

def run(cmd: str) -> str:
    """Run shell command, return output."""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5)
        return result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return "[timeout]"
    except Exception as e:
        return f"[error: {e}]"


def list_sessions() -> list[str]:
    """List tmux session names."""
    out = run("tmux list-sessions -F '#{session_name}' 2>/dev/null")
    if not out.strip() or "no server" in out:
        return []
    return [s.strip() for s in out.strip().split('\n') if s.strip()]


def capture_screen(session: str, lines: int = 100) -> str:
    """Capture full screen content from a session's active pane."""
    return run(f"tmux capture-pane -t {session} -p -S -{lines} 2>/dev/null")


def get_all_screens(lines: int = 100) -> dict[str, str]:
    """Get screen content from all tmux sessions."""
    screens = {}
    for session in list_sessions():
        content = capture_screen(session, lines)
        if content.strip():
            screens[session] = content
    return screens


def send_keys(keys: str, session: str = None, window: str = None) -> str:
    """Send keys to tmux pane."""
    target = ""
    if session:
        target = f"-t {session}"
        if window:
            target = f"-t {session}:{window}"

    escaped = keys.replace("'", "'\\''")
    return run(f"tmux send-keys {target} '{escaped}' Enter 2>/dev/null") or "sent"


def new_session(name: str, cmd: str = None) -> str:
    """Create new tmux session."""
    base = f"tmux new-session -d -s {name}"
    if cmd:
        base += f" '{cmd}'"
    return run(base)
