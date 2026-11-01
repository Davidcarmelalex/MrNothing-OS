#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
echo "MrNothing Phase 1 preflight"
python3 -m compileall -q core tests
python3 -m unittest discover -s tests -p 'test_*.py' -v
echo "All discovered Python tests passed."
echo "Android APK build is verified separately by GitHub Actions."
