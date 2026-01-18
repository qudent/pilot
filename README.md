# Post-UI Dev Server

Voice/text control for a remote dev server. Speak or type commands from your phone, Gemini Flash translates them to tmux actions.

## Architecture

```
Phone → HTTPS → Caddy → WebSocket → Pilot → Gemini Flash → tmux/agents
                                      ↓
                              context.md (rolling state)
```

## Quick Install

```bash
git clone https://github.com/qudent/post-ui-dotfiles.git
cd post-ui-dotfiles
./install.sh
```

## Structure

```
pilot/           # Main server (symlinked to ~/pilot at runtime)
  server.py      # WebSocket endpoint
  gemini.py      # Multimodal translation
  tmux.py        # tmux control
  context.py     # Rolling context
  static/        # Web client
  .venv/         # Python venv (gitignored, created by uv sync)

install.sh       # Creates ~/pilot symlink and installs services
tmux.conf        # Agent-friendly tmux config
bashrc.append    # PATH exports
claude.md        # Context for Claude Code sessions
```

## Usage

1. Open `https://YOUR_SERVER_IP` in browser (accept self-signed cert)
2. Enter token: `cat ~/.pilot/token`
3. Type or speak commands:
   - "check the build"
   - "run tests"
   - "show what's in the main pane"


## Required

```bash
export GEMINI_API_KEY=...      # For command translation
export ANTHROPIC_API_KEY=...   # For coding agents
```

## Services

```bash
sudo systemctl status pilot    # Voice control server
sudo systemctl status caddy    # HTTPS reverse proxy
```
