# SARVAM-001: explicit cloud text provider

User requirement: use Sarvam AI models. Isolated feature work from phase1 anchor
f42af837bcb8eed478cadbc472b7571441449a7a; no changes to other draft stacks.

Implements a stdlib Python text provider and owner-invoked stdin smoke client.
Default model sarvam-105b; sarvam-105b-conversations is explicitly allowlisted.
Fixed HTTPS api.sarvam.ai/v2/chat/completions using api-subscription-key;
SARVAM_API_KEY is read from the operator's environment, never committed or
embedded in Android. No OpenAI credentials/SDK are needed. No provider fallback,
model download, automatic retry, redirect or ambient proxy is used.

Official references checked 17 November 2026:
- https://docs.sarvam.ai/api-reference/chat/chat-completions-v2
- https://docs.sarvam.ai/api-reference/authentication

After configuring SARVAM_API_KEY securely in the intended Python runtime, invoke
`python scripts/sarvam_chat.py --allow-cloud` and provide synthetic text on stdin.
The flag explicitly permits that prompt to leave the machine for Sarvam. The
client reads at most 8193 characters, validates limits and returns text only.
No key is available in this authoring session; no live request was executed.
No claim about account credit, model availability or measured latency is made.

The library requires trusted application cloud_opt_in=True, not an assertion
from an agent or incoming request. This is not durable owner authentication or
per-action consent. UI integration needs visible disclosure and revocation.
All phone operations still require the existing independent authorization chain.
Model output is untrusted text; no tools, shell, enrollment or dispatch are wired.
The Android app's existing permission and StrongBox requirements are preserved.
Sarvam models are remote in this implementation, not on-device ROM components.

Bounds: prompt 8192 characters, generation 1-2048 tokens, response 1 MiB,
returned text 32768 characters, 20-second socket operation timeout. The timeout
is not a hard end-to-end deadline; trickle responses and cancellation require
a separate runtime deadline design before production integration. Partial/tool
responses, unexpected models, HTTP errors and malformed data fail closed.
No prompt, response body or credential is logged by the library. CLI prints the
requested reply; callers must choose an appropriate private terminal/session.

Verification: 10 mocked network regression tests passed locally. They verify
TLS destination, explicit opt-in before networking, key/header validation,
bounds, no redirects/retries, model mismatch, truncated/tool output refusal and
content-free errors. Mocked tests are not live provider or hardware evidence.
Hosted full Python/Android CI and independent non-author review remain separate.

Next: securely configure a key and run a synthetic live request, then add
independently tested Sarvam STT/TTS adapters with exact model/language/audio
limits, explicit microphone/upload consent and cancellation. No microphone,
audio upload, telephony or speech integration is implemented in this change.
Do not replace PaperClip's local-only inference with implicit cloud calls.

ROM inputs/licensing, adequate build infrastructure, integrated executor,
physical device validation and production OTA/release remain unresolved.
M1/M2/M6 in progress; M3 partial; M4/M5 unaccepted; M7/M8 blocked. 0/8 accepted.
No flash, unlock, root, production signing, merge or deployment.
