#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
echo "MrNothing Phase 1 preflight"
python3 -m unittest discover -s tests -p 'test_*policy.py' -v
python3 -m unittest discover -s tests -p 'test_hermes_gateway.py' -v
python3 -m unittest discover -s tests -p 'test_command_security.py' -v
echo "Local policy, Hermes adapter and command security checks passed."
echo "Android APK build is verified separately by GitHub Actions."
