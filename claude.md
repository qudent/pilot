# Claude Code Instructions

**Dotfiles repo**: https://github.com/qudent/post-ui-dotfiles (private)

## Package Managers

- **JavaScript/Node**: Use `pnpm`, not npm
- **Python**: Use `uv`, not pip

## About This File

This file should contain rough context about current work. Update when direction changes.

---

## Current Project: Pilot

Voice/text control for the dev server. Architecture:

```
Phone → HTTPS → Caddy → WebSocket → Pilot → Gemini Flash → tmux/agents
                                      ↓
                              ~/.pilot/context.md (rolling)
```

### Services

| Service | Port | Status |
|---------|------|--------|
| Pilot | 7777 (internal) | `systemctl status pilot` |
| Caddy | 443 (HTTPS) | `systemctl status caddy` |

### Key Files

```
~/pilot/
  server.py      # WebSocket server
  gemini.py      # Multimodal command translation
  tmux.py        # tmux control
  context.py     # Rolling context management
  static/        # Web client

~/.pilot/
  token          # Auth token (generated once)
  context.md     # Live rolling context
```

### Commands

```bash
pilot token      # Show auth token
pilot status     # Check if running
sudo systemctl restart pilot  # Restart
```

### Access

- **URL**: https://46.224.212.39 (self-signed cert, accept warning)
- **IPv6**: `2a01:4f8:1c1a:3385::1`
- **Token**: `cat ~/.pilot/token`
- Enter token in web client, stored in localStorage

### Installed Tools

| Tool | Command |
|------|---------|
| aider | `aider` |
| codex | `codex` |
| interpreter | `interpreter` |
| browser-use | `browser-use` |
| playwright | `playwright` |

### Required API Keys

```bash
export GEMINI_API_KEY=...      # For pilot
export ANTHROPIC_API_KEY=...   # For agents
```
