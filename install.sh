#!/bin/bash
set -e

echo "Installing Post-UI Dev Server..."

# Create directories
mkdir -p ~/.pilot/logs ~/Downloads

# Install pilot
cp -r pilot ~/pilot
cd ~/pilot
~/.local/bin/uv sync

# Install systemd services
sudo cp pilot.service /etc/systemd/system/
sudo cp Caddyfile /etc/caddy/Caddyfile
sudo systemctl daemon-reload
sudo systemctl enable pilot caddy
sudo systemctl restart caddy

# Copy configs
cp tmux.conf ~/.tmux.conf
cp claude.md ~/claude.md

# Append to bashrc if not already present
if ! grep -q "Post-UI" ~/.bashrc 2>/dev/null; then
    echo "" >> ~/.bashrc
    cat bashrc.append >> ~/.bashrc
    echo "Added PATH exports to ~/.bashrc"
fi

# Generate token if not exists
if [ ! -f ~/.pilot/token ]; then
    python3 -c "import secrets; print(secrets.token_urlsafe(32))" > ~/.pilot/token
    chmod 600 ~/.pilot/token
fi

# Start pilot
sudo systemctl start pilot

echo ""
echo "Done!"
echo ""
echo "Access: https://$(hostname -I | awk '{print $1}')"
echo "Token:  $(cat ~/.pilot/token)"
echo ""
echo "Set your API keys:"
echo "  export GEMINI_API_KEY=..."
echo "  export ANTHROPIC_API_KEY=..."
