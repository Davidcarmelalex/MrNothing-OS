# QA-013 — insecure emulator owner-key enrollment denial

On a fresh disposable Android 35 emulator without a secure lock, QA-013
navigates from the launcher to the local enrollment screen and verifies
that tapping the enrollment button fails closed before any credential
prompt. The script checks emulator identity, records UI hierarchies and
a screenshot, and does not set credentials, generate keys or alter
permissions. Python tests exercise strict hierarchy parsing.

The acceptance gate requires a successful exact-commit GitHub emulator
workflow. Passing Python source tests alone does not verify Android
runtime behavior. This does not validate StrongBox, attestation,
physical Pixel 9 Pro, agent consent, release readiness or OTA.

Independent review remains pending. The upstream shared SKILL.md is
unverified; the project-specific adapter is preserved.
