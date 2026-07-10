<div align="center">

# **MrNothing OS**

### *Autonomous AI Agent OS for Android. Runs Locally. Zero Cloud. Zero Cost.*

[![Status](https://img.shields.io/badge/Status-Building-ff6600?style=flat-square)]()
[![License](https://img.shields.io/badge/License-MIT-0f0f0f?style=flat-square)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11+-3776ab?style=flat-square&logo=python&logoColor=white)]()
[![Android](https://img.shields.io/badge/Android-Termux-3ddc84?style=flat-square&logo=android&logoColor=white)]()
[![Kotlin](https://img.shields.io/badge/Kotlin-2.0-7f52ff?style=flat-square&logo=kotlin&logoColor=white)]()

**Your phone, liberated. Autonomous AI that lives on your device.**

[Architecture](#architecture) · [Agents](#agents) · [Install](#installation) · [Ecosystem](#ecosystem)

</div>

---

## What is MrNothing OS?

MrNothing OS is an autonomous AI agent operating system that runs entirely on Android via Termux. No cloud dependency. No subscription fees. No data leaves your device unless you explicitly choose.

It transforms your phone from a passive consumer device into an active intelligence hub — running agents that can research, communicate, automate tasks, and execute commands 24/7.

## Why MrNothing OS?

| Problem | MrNothing OS Solution |
|---------|----------------------|
| **Cloud AI costs money** | Runs entirely local — zero recurring cost |
| **Privacy concerns** | Your data never leaves your device |
| **Limited by app ecosystem** | Terminal-first, script anything |
| **Phone sits idle** | Runs autonomous agents 24/7 |
| **No unified AI control** | Single orchestration hub for all agents |

## Architecture

```
┌─────────────────────────────────────────────┐
│           MrNothing OS                      │
│           (Android + Termux)                │
│                                             │
│  ┌─────────────┐    ┌─────────────────┐    │
│  │  Core OS    │    │  Agent Manager  │    │
│  │  (Python)   │    │  (orchestrator) │    │
│  │             │    │                 │    │
│  │ - Boot seq  │    │ - Agent lifecycle│    │
│  │ - Config    │    │ - Task scheduling │    │
│  │ - Logging   │    │ - Inter-agent     │    │
│  │ - Updates   │    │   communication   │    │
│  └──────┬──────┘    └────────┬────────┘    │
│         │                     │              │
│  ┌──────┴─────────────────────┴──────┐       │
│  │           AGENT ECOSYSTEM          │       │
│  │                                     │       │
│  │  ┌──────────┐    ┌──────────────┐  │       │
│  │  │ HERMES   │    │  OPENCLAW    │  │       │
│  │  │ (comms)  │    │  (security)  │  │       │
│  │  └──────────┘    └──────────────┘  │       │
│  │  ┌──────────┐    ┌──────────────┐  │       │
│  │  │PAPERCLIP │    │   AGENT47    │  │       │
│  │  │ (tasks)  │    │   (ops)      │  │       │
│  │  └──────────┘    └──────────────┘  │       │
│  │  ┌──────────┐    ┌──────────────┐  │       │
│  │  │  MSEAL   │    │    WEB3      │  │       │
│  │  │ (p2p)    │    │  (wallet)    │  │       │
│  │  └──────────┘    └──────────────┘  │       │
│  └─────────────────────────────────────┘       │
└─────────────────────────────────────────────┘
```

## Agents

| Agent | Function | Status | Language |
|-------|----------|--------|----------|
| **HERMES** | Executive orchestrator — routes commands, manages session state | 🚧 Core | Python |
| **OPENCLAW** | Security reconnaissance — network scanning, threat detection | 🚧 Building | Python |
| **PAPERCLIP** | Task automation — scheduling, reminders, file ops | 🚧 Building | Python |
| **AGENT47** | Silent operations — background intelligence gathering | 📋 Planned | Python |
| **MSEAL** | P2P encrypted communications — secure messaging | 📋 Planned | Python + Kotlin |
| **WEB3** | Crypto wallet — sovereign key management | 📋 Planned | Python |

## Modules

```
modules/
├── voice/              # Voice recognition and synthesis
├── nlp/               # Natural language processing
├── vision/            # Computer vision (camera access)
├── sensors/           # Device sensor integration
├── network/           # Network tools and monitoring
├── storage/           # Local database and file management
└── security/          # Encryption, auth, sandboxing
```

## Installation

### Prerequisites

- Android 8.0+ with Termux installed
- 2GB free storage
- Python 3.11+ in Termux

### Termux Setup

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

# View logs
tail -f logs/system.log
```

## Core Commands

```bash
# Agent management
python core/cli.py agent start hermes
python core/cli.py agent stop openclaw
python core/cli.py agent restart paperclip

# System status
python core/cli.py status
python core/cli.py logs
python core/cli.py config

# Task execution
python core/cli.py task "scan network"
python core/cli.py task "check security"
```

## Tech Stack

- **Runtime:** Python 3.11+ · asyncio
- **Platform:** Android via Termux
- **AI:** Ollama (local LLM) · Whisper (STT) · Coqui (TTS)
- **Security:** AES-256-GCM · Argon2 · Ed25519
- **Storage:** SQLite · JSON config
- **Network:** aiohttp · scapy · socket

## Ecosystem

MrNothing OS is part of the **M&R&Nothing** ecosystem:

```
M&R&Nothing Ecosystem
├── MrNothing OS (this repo)    # Autonomous AI OS for Android
├── MR//NOTHING                 # Luxury streetwear
├── mSeal (hermeslock)          # Encrypted messaging
├── VOID//SIGNAL                # Autonomous AI news
├── FactLogic                   # Myth-busting engine
├── Nexum Labs                  # Gamified learning
├── Jan Niti                    # Civic transparency
├── NothingBuilt                # Artist sovereignty
├── NothingOS                   # Wearable hub
├── Nothing Hustle              # AI gig orchestrator
├── VOID.Bounty                 # Bug bounty platform
└── PartHive                    # UAE auto parts
```

→ [github.com/Davidcarmelalex/MrNothingEcosystem](https://github.com/Davidcarmelalex/MrNothingEcosystem)

---

*Built from nothing. For someone. Forever.*
*MR° · M&R&Nothing · 2026 · A tribute, by David Carmel Alex*
