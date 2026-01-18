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
- server.py - WebSocket endpoint with debug logging
- gemini.py - Structured output via Pydantic + Gemini response_schema
- tmux.py - tmux control
- context.py - Rolling context
- config.py - Auth, paths, user prompt loading
- test_pilot.py - pytest test suite

## Customization
- `~/.pilot/prompt.md` - Custom instructions for Gemini (optional)
- `PILOT_DEBUG=1` - Enable debug logging to ~/.pilot/logs/pilot.log

## Runtime
- `~/pilot` symlinks to this repo's `pilot/` directory
- `.venv/` and `uv.lock` live in `pilot/` (gitignored)

## Testing
```bash
cd pilot && uv run pytest test_pilot.py -v
```
