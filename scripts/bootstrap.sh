#!/data/data/com.termux/files/usr/bin/bash
# MrNothing OS Bootstrap Script
# Runs after Termux installation to set up the full environment

set -e

MN_HOME="$HOME/mrnothing"
MN_BIN="$HOME/.local/bin"
GITHUB_BASE="https://raw.githubusercontent.com/Davidcarmelalex/MrNothing-OS/main"

log() { echo "[$(date +%H:%M:%S)] $1"; }
notify() { termux-notification --title "MrNothing" --content "$1" 2>/dev/null || true; }

log "════════════════════════════════════"
log " MrNothing OS Bootstrap v1.0"
log "════════════════════════════════════"

# Step 1: Update packages
log "Updating package lists..."
pkg update -y 2>/dev/null || true

# Step 2: Install core packages
log "Installing core packages..."
pkg install -y python python-pip nodejs git curl wget nano \
    termux-api openssh nmap 2>/dev/null || {
    log "Some packages may have failed — continuing..."
}

# Step 3: Install Python dependencies
log "Installing Python packages..."
pip install --quiet --upgrade pip 2>/dev/null || true
pip install --quiet requests pathlib 2>/dev/null || true

# Step 4: Create directory structure
log "Creating MrNothing directory tree..."
mkdir -p "$MN_HOME"/{agents,modules,models,logs,reports,wallet,config,audio,bin}
mkdir -p "$MN_HOME/agents"/{hermes,paperclip,openclaw}
mkdir -p "$MN_HOME/modules"/{web3-wallet,voice-engine,whatsapp,network}

# Step 5: Download core files
log "Downloading MrNothing core..."
CORE_URLS=(
    "core/main.py|$MN_HOME/core.py"
    "agents/hermes/agent.py|$MN_HOME/agents/hermes/agent.py"
    "agents/paperclip/agent.py|$MN_HOME/agents/paperclip/agent.py"
    "agents/openclaw/agent.py|$MN_HOME/agents/openclaw/agent.py"
    "modules/web3-wallet/wallet.py|$MN_HOME/modules/web3-wallet/wallet.py"
    "modules/voice-engine/voice.py|$MN_HOME/modules/voice-engine/voice.py"
)

for entry in "${CORE_URLS[@]}"; do
    src="${entry%%|*}"
    dst="${entry##*|}"
    url="$GITHUB_BASE/$src"
    log "Downloading: $src"
    curl -sL "$url" -o "$dst" || log "WARNING: Failed to download $src"
done

# Step 6: Create CLI wrapper
mkdir -p "$MN_BIN"
cat > "$MN_BIN/mrnothing" << 'WRAPPER'
#!/data/data/com.termux/files/usr/bin/bash
python3 "$HOME/mrnothing/core.py" "$@"
WRAPPER
chmod +x "$MN_BIN/mrnothing"
ln -sf "$MN_BIN/mrnothing" "$MN_BIN/mn" 2>/dev/null || true

# Step 7: Add to PATH
if ! grep -q "mrnothing" "$HOME/.bashrc" 2>/dev/null; then
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc"
    echo 'echo "[MrNothing OS] Type: mrnothing"' >> "$HOME/.bashrc"
fi

# Step 8: Auto-boot on Termux start
mkdir -p "$HOME/.termux/boot"
cat > "$HOME/.termux/boot/start-mrnothing.sh" << 'BOOT'
#!/data/data/com.termux/files/usr/bin/bash
termux-wake-lock
termux-notification --title "MrNothing OS" --content "Agent core booting..." 2>/dev/null
sleep 5
python3 "$HOME/mrnothing/agents/hermes/agent.py" --daemon &
BOOT
chmod +x "$HOME/.termux/boot/start-mrnothing.sh"

# Step 9: Default config
cat > "$MN_HOME/config.json" << 'CONFIG'
{
  "version": "1.0.0",
  "agents_enabled": ["hermes", "paperclip"],
  "voice_enabled": false,
  "web3_enabled": false,
  "auto_boot": true,
  "log_level": "INFO"
}
CONFIG

log ""
log "════════════════════════════════════"
log " ✅ MrNothing OS Bootstrap Complete"
log "════════════════════════════════════"
log " Type: mrnothing"
log " Or:   mn"
log ""
notify "MrNothing OS installed. Type: mrnothing"
source "$HOME/.bashrc" 2>/dev/null || true
