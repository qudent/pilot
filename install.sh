#!/bin/bash
set -e

echo "Installing Post-UI Agent Server dotfiles..."

# Create directories
mkdir -p ~/bin ~/.browser-profile ~/Downloads

# Copy scripts
cp bin/* ~/bin/
chmod +x ~/bin/*

# Copy tmux config
cp tmux.conf ~/.tmux.conf

# Copy claude.md
cp claude.md ~/claude.md

# Append to bashrc if not already present
if ! grep -q "Post-UI Agent Server" ~/.bashrc 2>/dev/null; then
    echo "" >> ~/.bashrc
    cat bashrc.append >> ~/.bashrc
    echo "Added PATH exports to ~/.bashrc"
else
    echo "PATH exports already in ~/.bashrc"
fi

echo ""
echo "Done! Now install the tools:"
echo ""
echo "  # Python package manager"
echo "  curl -LsSf https://astral.sh/uv/install.sh | sh"
echo ""
echo "  # Node package manager"
echo "  npm i -g pnpm && pnpm setup"
echo ""
echo "  # Agents"
echo "  uv tool install aider-chat"
echo "  uv tool install browser-use --with langchain-anthropic"
echo "  uv tool install playwright && playwright install chromium --with-deps"
echo "  uv tool install open-interpreter"
echo "  pnpm add -g @openai/codex"
echo ""
echo "  # GitHub CLI auth"
echo "  gh auth login"
echo ""
echo "Reload shell: source ~/.bashrc"
