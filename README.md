# MrNothing OS 🖤

> *"Nothing runs everything."*

**MrNothing OS** is a fully autonomous, locally-running AI agent stack for Android via Termux. Zero cloud dependencies. Zero API costs. Runs on your phone CPU.

---

## ⚡ One-Command Install

Open Termux and run:
```bash
curl -sL https://raw.githubusercontent.com/Davidcarmelalex/MrNothing-OS/main/scripts/bootstrap.sh | bash
```

Then launch:
```bash
mrnothing
```

---

## 🧠 Architecture

```
MrNothing OS
├── core.py              ← Command brain (main loop)
├── agents/
│   ├── hermes/          ← Task automation + notifications
│   ├── paperclip/       ← Local AI reasoning (Whisper/TinyLlama)
│   └── openclaw/        ← Network security intelligence
├── modules/
│   ├── web3-wallet/     ← Self-custodial EVM wallet
│   ├── voice-engine/    ← Whisper STT + Android TTS
│   ├── whatsapp/        ← WhatsApp automation (Node.js)
│   └── network/         ← Network scanning + OSINT
└── scripts/
    └── bootstrap.sh     ← One-shot installer
```

---

## 💰 Total Cost

| Component | Cost |
|-----------|------|
| This repo | $0 |
| Termux | $0 |
| All AI models | $0 (local) |
| Cloud APIs | $0 (none used) |
| **Total** | **$0** |

---

## 🤖 Agents

### Hermes — Task Automation
Schedules and executes shell tasks. Sends push notifications via Termux API.
```bash
python3 ~/mrnothing/agents/hermes/agent.py
```

### PaperClip — Local AI
Runs TinyLlama or any GGUF model locally. No internet required.
```bash
python3 ~/mrnothing/agents/paperclip/agent.py
```
Drop any `.gguf` model into `~/mrnothing/models/` to power it up.

### OpenClaw — Security Intelligence
Network scanning, port analysis, dark web OSINT hooks.
```bash
python3 ~/mrnothing/agents/openclaw/agent.py
```

---

## 📦 Modules

### Web3 Wallet
Self-custodial ETH wallet. Keys never leave your device.
```bash
python3 ~/mrnothing/modules/web3-wallet/wallet.py
```

### Voice Engine
OpenAI Whisper (open source) for STT. Android native TTS.
```bash
python3 ~/mrnothing/modules/voice-engine/voice.py
```

### WhatsApp Bot
Autonomous WhatsApp agent via whatsapp-web.js.
```bash
python3 ~/mrnothing/modules/whatsapp/whatsapp.py
```

---

## 📋 Requirements

- Android 7+ with ADB sideloading enabled
- Termux (F-Droid version)
- termux-api installed
- 2GB free storage (for ML models)
- WiFi for initial setup

---

## ⚖️ License

MIT — Free forever. Build on it.

---

*Part of the MrNothing Autonomous Enterprise ecosystem.*  
*Built by [David Carmel Alex](https://github.com/Davidcarmelalex) — Architect of the MrNothing movement.*
