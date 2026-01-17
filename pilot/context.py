"""Rolling context management - keeps context.md bounded."""
import time
from datetime import datetime
from pathlib import Path
from config import CONTEXT_FILE, CONTEXT_MAX_LINES

def load() -> str:
    """Load current context."""
    if CONTEXT_FILE.exists():
        return CONTEXT_FILE.read_text()
    return ""


def save(content: str):
    """Save context, truncating if needed."""
    lines = content.strip().split('\n')
    if len(lines) > CONTEXT_MAX_LINES:
        # Keep header + last N lines
        header = lines[:5]  # Keep first 5 lines (title, current task)
        tail = lines[-(CONTEXT_MAX_LINES - 5):]
        lines = header + ["", "... (truncated)", ""] + tail

    CONTEXT_FILE.write_text('\n'.join(lines))


def update(task: str = None, files: list[str] = None, note: str = None, state: dict = None):
    """Update context with new information."""
    now = datetime.now().strftime("%H:%M")

    content = load()
    lines = content.split('\n') if content else []

    # Find or create sections
    sections = {
        "task": None,
        "files": None,
        "state": None,
        "log": None
    }

    new_lines = [f"# Pilot Context", f"_Updated: {now}_", ""]

    # Current task
    if task:
        new_lines += [f"## Current Task", task, ""]
    elif "## Current Task" in content:
        # Preserve existing task
        idx = content.find("## Current Task")
        end = content.find("\n## ", idx + 1)
        if end == -1:
            end = len(content)
        task_section = content[idx:end].strip()
        new_lines += [task_section, ""]

    # Recent files
    new_lines += ["## Recent Files"]
    if files:
        for f in files[-10:]:  # Last 10 files
            new_lines.append(f"- `{f}`")
    new_lines.append("")

    # Server state
    if state:
        new_lines += ["## Server State"]
        if state.get("sessions"):
            for sess in state["sessions"]:
                new_lines.append(f"- **{sess['name']}**: {', '.join(sess['windows'][:3])}")
        else:
            new_lines.append("- No tmux sessions")
        new_lines.append("")

    # Activity log (rolling)
    new_lines += ["## Activity Log"]
    if note:
        new_lines.append(f"- [{now}] {note}")

    # Preserve recent log entries
    if "## Activity Log" in content:
        idx = content.find("## Activity Log")
        log_section = content[idx:].split('\n')[1:]  # Skip header
        recent = [l for l in log_section if l.startswith("- [")][-15:]  # Last 15
        new_lines += recent

    save('\n'.join(new_lines))


def init(gps: dict = None):
    """Initialize context for new session."""
    content = ["# Pilot Context", f"_Started: {datetime.now().strftime('%Y-%m-%d %H:%M')}_", ""]

    if gps:
        content += [f"## Location", f"GPS: {gps.get('lat', '?')}, {gps.get('lon', '?')}", ""]

    content += [
        "## Current Task",
        "(none)",
        "",
        "## Server State",
        "(initializing)",
        "",
        "## Activity Log",
        f"- [{datetime.now().strftime('%H:%M')}] Session started",
    ]

    save('\n'.join(content))
    return '\n'.join(content)
