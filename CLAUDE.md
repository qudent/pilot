# CLAUDE.md

Pilot - Voice/text control server for remote dev environments. Speak or type commands, Gemini Flash translates them to tmux actions.

## Architecture
Phone -> HTTPS -> Caddy -> WebSocket -> Pilot -> Gemini Flash -> tmux/agents

## Setup
```bash
./install.sh   # Creates ~/pilot symlink -> ./pilot, installs services
export GEMINI_API_KEY=...
export ANTHROPIC_API_KEY=...
```

## Key Files (in pilot/)
- server.py - WebSocket endpoint
- gemini.py - Multimodal translation
- tmux.py - tmux control
- context.py - Rolling context

## Runtime
- `~/pilot` symlinks to this repo's `pilot/` directory
- `.venv/` and `uv.lock` live in `pilot/` (gitignored)
