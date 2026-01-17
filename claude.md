# Claude Code Instructions

## Package Managers

- **JavaScript/Node**: Use `pnpm`, not npm
- **Python**: Use `uv`, not pip

## About This File

This file (claude.md) should contain rough context about what we've been working on. Update it when the project direction changes or significant progress is made.

---

## Current Context

### Project: Post-UI Agent Server

Setting up this Hetzner server as a voice-controlled development machine. The vision:

1. **Voice input** from smartphone/other surfaces
2. **Gemini Flash** translates voice commands/drawings/pictures into commands
3. **tmux** sessions receive and execute commands
4. **Heavy-hitting Claude instances** do the actual coding work
5. **Browser automation** enables agents to research (flights, docs, etc.)

### What's Installed

| Tool | Command | Purpose |
|------|---------|---------|
| Claude Code | `claude` | Main coding agent |
| aider | `aider` | AI pair programming |
| Codex CLI | `codex` | OpenAI's coding agent |
| Open Interpreter | `interpreter` | Natural language → code |
| Playwright | `playwright` | Browser automation |
| browser-use | `browser-use` | LLM-controlled browsing |
| uv | `uv` | Fast Python package manager |
| pnpm | `pnpm` | Fast Node package manager |

### Configuration Done

- `~/.bashrc` - PATH includes `~/bin`, `~/.local/bin`, `~/.local/share/pnpm`, `~/.npm-global/bin`
- `~/.tmux.conf` - Agent-friendly config (C-a prefix, mouse, 50k scrollback)
- `~/.browser-profile/` - Persistent browser profile (cookies, localStorage, logins)
- GitHub authenticated as `qudent`

### Browser Scripts

- `browser` - Launch persistent Chromium (maintains login sessions)
- `browse "task"` - Run browser-use agent with persistent profile

The browser uses `~/.browser-profile/` to persist cookies and logins across sessions - not ephemeral like test browsers.

### Next Steps

- Set up voice → Gemini → tmux command pipeline
- Configure API keys (ANTHROPIC_API_KEY, etc.)
