# Post-UI Agent Server Dotfiles

Configuration for a voice-controlled development server running AI coding agents.

## Quick Install

```bash
./install.sh
```

## What's Included

### Scripts (`bin/`)
- `browser` - Persistent Chromium browser (maintains cookies/logins across sessions)
- `browse "task"` - Run browser-use agent with persistent profile

### Configs
- `tmux.conf` - Agent-friendly tmux (C-a prefix, mouse, 50k scrollback)
- `bashrc.append` - PATH exports for uv, pnpm, custom scripts

### Context
- `claude.md` - Project context for Claude Code sessions

## Architecture

```
Voice/Images → Gemini Flash → tmux commands → Claude/Agents → Browser automation
     ↑                                              ↓
 Smartphone                                   Flight research, etc.
```

## Installed Tools

| Tool | Install | Purpose |
|------|---------|---------|
| uv | `curl -LsSf https://astral.sh/uv/install.sh \| sh` | Python packages |
| pnpm | `npm i -g pnpm && pnpm setup` | Node packages |
| aider | `uv tool install aider-chat` | AI pair programming |
| browser-use | `uv tool install browser-use --with langchain-anthropic` | LLM browser control |
| playwright | `uv tool install playwright && playwright install chromium --with-deps` | Browser automation |
| open-interpreter | `uv tool install open-interpreter` | Natural language → code |
| codex | `pnpm add -g @openai/codex` | OpenAI coding agent |

## Required API Keys

Set in `~/.bashrc` or `~/.env`:
```bash
export ANTHROPIC_API_KEY=sk-ant-...
export OPENAI_API_KEY=sk-...
```
