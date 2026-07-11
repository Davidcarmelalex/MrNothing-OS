<div align="center">

<img src="https://capsule-render.vercel.app/api?type=venom&color=0f0f0f&height=200&section=header&text=MrNothing%20OS&fontSize=60&fontColor=7f52ff&animation=fadeIn&fontAlignY=38&desc=Autonomous%20AI%20Agent%20OS%20for%20Android%20%E2%80%94%20Runs%20Locally.%20Zero%20Cloud.%20Zero%20Cost.&descAlignY=58&descSize=16&descColor=cccccc" width="100%"/>

<br/>

<img src="https://readme-typing-svg.herokuapp.com?font=JetBrains+Mono&size=16&duration=3000&pause=1000&color=7f52ff&center=true&vAlign=true&width=900&lines=Your+phone%2C+liberated.+%E2%80%94+Autonomous+AI+that+lives+on+your+device.;Local+LLM+via+Ollama+%C2%B7+Voice+AI+%C2%B7+Security+audit+%C2%B7+24%2F7+agents;Transform+your+phone+from+a+consumer+device+into+an+intelligence+hub." />

<br/><br/>

[![Status](https://img.shields.io/badge/Status-Beta-ffcc00?style=for-the-badge&logo=testinglibrary&logoColor=white)]()
[![Version](https://img.shields.io/badge/Version-0.9.0-7f52ff?style=for-the-badge&logo=semver&logoColor=white)]()
[![License](https://img.shields.io/badge/License-MIT-0f0f0f?style=for-the-badge&logo=opensourceinitiative&logoColor=white)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11+-3776ab?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Android](https://img.shields.io/badge/Android-Termux-3ddc84?style=for-the-badge&logo=android&logoColor=white)](https://termux.dev)
[![Kotlin](https://img.shields.io/badge/Kotlin-2.0-7f52ff?style=for-the-badge&logo=kotlin&logoColor=white)](https://kotlinlang.org)

<br/>

<a href="https://github.com/Davidcarmelalex/MrNothing-OS/stargazers"><img src="https://img.shields.io/github/stars/Davidcarmelalex/MrNothing-OS?style=flat-square&color=7f52ff" /></a>
<a href="https://github.com/Davidcarmelalex/MrNothing-OS/network/members"><img src="https://img.shields.io/github/forks/Davidcarmelalex/MrNothing-OS?style=flat-square&color=7f52ff" /></a>
<a href="https://github.com/Davidcarmelalex/MrNothing-OS/issues"><img src="https://img.shields.io/github/issues/Davidcarmelalex/MrNothing-OS?style=flat-square&color=7f52ff" /></a>

</div>

---

## What is MrNothing OS?

**MrNothing OS** is an autonomous AI agent operating system that runs entirely on Android via Termux. No cloud dependency. No subscription fees. No data leaves your device unless you explicitly choose.

It transforms your phone from a passive consumer device into an active intelligence hub — running agents that can research, communicate, automate tasks, and execute commands 24/7.

> **🔒 Security First:** Every MrNothing OS installation includes [MrNothing Shield](https://github.com/Davidcarmelalex/mrnothing-shield) integration for built-in spyware detection and permission auditing.

## Why MrNothing OS?

| Problem | MrNothing OS Solution |
|---------|----------------------|
| **Cloud AI costs money** | Runs entirely local — zero recurring cost |
| **Privacy concerns** | Your data never leaves your device |
| **Limited by app ecosystem** | Terminal-first, script anything |
| **Phone sits idle** | Runs autonomous agents 24/7 |
| **No unified AI control** | Single orchestration hub for all agents |
| **Spyware & surveillance** | Integrated Shield security audit framework |

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────────────┐
│                           MrNothing OS v0.9                               │
│                     (Android + Termux Environment)                        │
│                                                                           │
│  ┌───────────────────── CORE SYSTEM ──────────────────────┐              │
│  │                                                         │              │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │              │
│  │  │   Kernel     │  │    HERMES    │  │   Config     │  │              │
│  │  │   (Python)   │  │  Executive   │  │   Manager    │  │              │
│  │  │              │  │  Orchestrator│  │              │  │              │
│  │  │ · Boot seq   │  │              │  │ · Settings   │  │              │
│  │  │ · Scheduler  │  │ · Command    │  │ · Profiles   │  │              │
│  │  │ · Logging    │  │   routing    │  │ · Secrets    │  │              │
│  │  │ · Updates    │  │ · Session    │  │ · Backups    │  │              │
│  │  └──────┬───────┘  │   state      │  └──────┬───────┘  │              │
│  │         │           └──────┬───────┘         │           │              │
│  │         └──────────────────┼─────────────────┘           │              │
│  │                            │                              │              │
│  └────────────────────────────┼──────────────────────────────┘              │
│                               │                                             │
│  ┌────────────────────────────┼─────── AGENT ECOSYSTEM ───────────────────┐│
│  │                            │                                            ││
│  │  ┌──────────────┐  ┌─────┴──────────┐  ┌──────────────┐              ││
│  │  │   HERMES     │  │   PAPERCLIP    │  │   OPENCLAW   │              ││
│  │  │  Executive   │  │  Task Agent    │  │  Security    │              ││
│  │  │              │  │                │  │  Agent       │              ││
│  │  │ · Command    │  │ · Scheduling   │  │              │              ││
│  │  │   routing    │  │ · Reminders    │  │ · Root       │              ││
│  │  │ · NLP        │  │ · File ops     │  │   detection  │              ││
│  │  │   parsing    │  │ · Automation   │  │ · Permission │              ││
│  │  │ · Agent      │  │ · Notes        │  │   audit      │              ││
│  │  │   lifecycle  │  │ · Clipboard    │  │ · Network    │              ││
│  │  └──────┬───────┘  │   manager      │  │   monitor    │              ││
│  │         │           └────────────────┘  └──────┬───────┘              ││
│  │         │                                       │                      ││
│  │  ┌──────┴──────┐  ┌──────────────────┐  ┌─────┴──────────┐           ││
│  │  │   MSEAL     │  │     WEB3         │  │    SHIELD      │           ││
│  │  │  P2P Comms  │  │  Crypto Wallet   │  │  Security      │           ││
│  │  │             │  │                  │  │  Auditor       │           ││
│  │  │ · E2E       │  │ · Key mgmt       │  │              │           ││
│  │  │   encrypt   │  │ · Transactions   │  │ · Spyware    │           ││
│  │  │ · Mesh      │  │ · Multi-chain    │  │   detection  │           ││
│  │  │   network   │  │ · Signing        │  │ · Hidden app │           ││
│  │  └─────────────┘  │                  │  │   scanner    │           ││
│  │                   └──────────────────┘  │ · Forensic   │           ││
│  │                                         │   reports    │           ││
│  │                                         └──────────────┘           ││
│  └────────────────────────────────────────────────────────────────────┘│
│                                                                         │
│  ┌───────────────────── HARDWARE LAYER ──────────────────────────────┐ │
│  │                                                                    │ │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │ │
│  │  │  Voice   │ │  Camera  │ │  Sensors │ │  Network │           │ │
│  │  │(Whisper) │ │ (Vision) │ │(GPS/etc) │ │(WiFi/4G) │           │ │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘           │ │
│  └──────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Agents

| Agent | Function | Status | Language | Version |
|-------|----------|--------|----------|---------|
| **HERMES** | Executive orchestrator — routes commands, manages session state | ✅ **Core** | Python | v0.9 |
| **OPENCLAW** | Security reconnaissance — network scanning, threat detection, permission auditing | 🚧 **Building** | Python | v0.5 |
| **PAPERCLIP** | Task automation — scheduling, reminders, file ops, clipboard | 🚧 **Building** | Python | v0.4 |
| **SHIELD** | Mobile security audit — spyware detection, hidden app scanner, forensic reports | 🔥 **Active** | Python | v1.0 |
| **MSEAL** | P2P encrypted communications — secure messaging | 📋 Planned | Python + Kotlin | — |
| **WEB3** | Crypto wallet — sovereign key management | 📋 Planned | Python | — |

---

## Modules

```
modules/
├── voice/              # Voice recognition and synthesis (Whisper + Coqui)
├── nlp/               # Natural language processing (local LLM via Ollama)
├── vision/            # Computer vision (camera access, QR scanning)
├── sensors/           # Device sensor integration (GPS, accelerometer)
├── network/           # Network tools and monitoring
├── storage/           # Local database and file management
├── security/          # Encryption, auth, sandboxing, Shield integration
└── web3/              # Blockchain wallet and transaction signing
```

---

## Quick Start

### Prerequisites

- Android 8.0+ with Termux installed
- 2GB free storage
- Python 3.11+ in Termux

### One-Line Install

```bash
pkg update && pkg install python git -y && git clone https://github.com/Davidcarmelalex/MrNothing-OS.git && cd MrNothing-OS && pip install -r requirements.txt && python core/boot.py
```

### Manual Setup

```bash
# Update packages
pkg update && pkg upgrade -y

# Install Python and tools
pkg install python git -y

# Clone MrNothing OS
git clone https://github.com/Davidcarmelalex/MrNothing-OS.git
cd MrNothing-OS

# Install Python dependencies
pip install -r requirements.txt

# First boot
python core/boot.py
```

### Post-Install

```bash
# Start the OS
python core/boot.py --start

# Check agent status
python core/cli.py status

# Run security audit with Shield
python core/cli.py shield audit

# View logs
tail -f logs/system.log
```

---

## Core Commands

```bash
# Agent management
python core/cli.py agent start hermes
python core/cli.py agent stop openclaw
python core/cli.py agent restart paperclip
python core/cli.py agent restart shield

# System status
python core/cli.py status
python core/cli.py logs
python core/cli.py config

# Security audit (via Shield)
python core/cli.py shield audit --full
python core/cli.py shield scan --module permissions
python core/cli.py shield scan --module hidden_apps
python core/cli.py shield report --format pdf

# Task execution
python core/cli.py task "scan network"
python core/cli.py task "check security"
python core/cli.py task "audit permissions"
```

---

## Security Best Practices

MrNothing OS integrates [MrNothing Shield](https://github.com/Davidcarmelalex/mrnothing-shield) for continuous security monitoring:

1. **Run `shield audit` on first boot** — Detect any pre-existing spyware
2. **Schedule weekly audits** — Automated via Paperclip agent
3. **Review permission reports** — Revoke unnecessary app permissions
4. **Monitor network traffic** — Alert on suspicious outbound connections
5. **Keep Termux updated** — `pkg upgrade` weekly

---

## Tech Stack

- **Runtime:** Python 3.11+ · asyncio
- **Platform:** Android via Termux
- **AI:** Ollama (local LLM) · Whisper (STT) · Coqui (TTS)
- **Security:** AES-256-GCM · Argon2 · Ed25519 · MrNothing Shield
- **Storage:** SQLite · JSON config
- **Network:** aiohttp · scapy · socket

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Termux crashes on boot | Increase RAM allocation in Android settings |
| Ollama won't start | Ensure 1GB+ free storage, reinstall: `pkg reinstall ollama` |
| Agents not responding | Check logs: `python core/cli.py logs` |
| Permission denied | Run `termux-setup-storage` and grant file access |
| Shield scan fails | Ensure ADB is configured: `pkg install android-tools` |

---

## Ecosystem

MrNothing OS is part of the **M&R&Nothing** ecosystem:

```
M&R&Nothing Ecosystem
├── MrNothing OS (this repo)     # Autonomous AI OS for Android
├── MrNothing Shield             # Mobile security audit framework
├── MR//NOTHING                  # Luxury streetwear drops
├── mSeal (hermeslock)           # Encrypted messaging
├── VOID//SIGNAL                 # Autonomous AI news
├── FactLogic                    # Myth-busting engine
├── Nexum Labs                   # Gamified learning
├── Jan Niti                     # Civic transparency
├── NothingBuilt                 # Artist sovereignty
├── NothingOS                    # Wearable hub
├── Nothing Hustle               # AI gig orchestrator
├── VOID.Bounty                  # Bug bounty platform
└── PartHive                     # UAE auto parts
```

→ [github.com/Davidcarmelalex/MrNothingEcosystem](https://github.com/Davidcarmelalex/MrNothingEcosystem)

---

*Built from nothing. For someone. Forever.*
*MR° · M&R&Nothing · 2026 · A tribute, by David Carmel Alex*

<img src="https://capsule-render.vercel.app/api?type=waving&color=0f0f0f&height=80&section=footer" width="100%"/>
