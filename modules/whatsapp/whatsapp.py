#!/usr/bin/env python3
"""
MrNothing WhatsApp Module
Uses whatsapp-web.js via Node.js (headless WhatsApp Web).
Requires Node.js + npm to be installed.
"""
import subprocess, json, os, time
from pathlib import Path

HOME = Path.home() / "mrnothing"
WA_DIR = HOME / "modules" / "whatsapp"
WA_JS = WA_DIR / "wa-bot.js"

WA_BOT_JS = '''
const { Client, LocalAuth } = require('whatsapp-web.js');
const qrcode = require('qrcode-terminal');

const client = new Client({
    authStrategy: new LocalAuth({ dataPath: process.env.HOME + '/mrnothing/modules/whatsapp/session' })
});

client.on('qr', qr => {
    console.log('\\n[MRNOTHING] Scan this QR code with WhatsApp:');
    qrcode.generate(qr, { small: true });
});

client.on('ready', () => {
    console.log('[MRNOTHING] WhatsApp connected!');
    require('fs').writeFileSync('/tmp/wa_ready', '1');
});

client.on('message', msg => {
    const body = msg.body.toLowerCase();
    if (body === '!ping') msg.reply('pong — MrNothing OS online');
    if (body === '!status') msg.reply('MrNothing OS running. All agents nominal.');
    if (body === '!help') msg.reply('Commands:\\n!ping — check status\\n!status — agent status');
});

client.initialize();
'''

def setup_nodejs():
    result = subprocess.run("which node", shell=True, capture_output=True)
    if result.returncode != 0:
        print("Node.js not found. Run: pkg install nodejs")
        return False
    WA_DIR.mkdir(parents=True, exist_ok=True)
    WA_JS.write_text(WA_BOT_JS)
    os.chdir(WA_DIR)
    print("Installing whatsapp-web.js (one-time, ~2min)...")
    subprocess.run("npm install whatsapp-web.js qrcode-terminal", shell=True)
    return True

def start_bot():
    if not WA_JS.exists():
        if not setup_nodejs():
            return
    print("\n[WHATSAPP] Starting bot — scan QR in WhatsApp...\n")
    subprocess.run(f"node {WA_JS}", shell=True)

def main():
    print("\n[WHATSAPP MODULE v1.0]")
    print("Commands: setup, start, exit\n")
    while True:
        try:
            cmd = input("whatsapp> ").strip()
            if cmd == "exit": break
            elif cmd == "setup": setup_nodejs()
            elif cmd == "start": start_bot()
            else: print("Commands: setup, start, exit")
        except (KeyboardInterrupt, EOFError): break

if __name__ == "__main__":
    main()
