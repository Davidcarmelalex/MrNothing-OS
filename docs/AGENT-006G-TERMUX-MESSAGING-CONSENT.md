# AGENT-006G — Termux messaging consent boundary

Status: Implemented on feat/phase1-agentic-phone; exact-head CI pending at initial commit.

## Scope

This change hardens the isolated legacy modules/whatsapp/whatsapp.py module. It does not connect WhatsApp or SMS to HERMES, the Kotlin launcher, Android CommandRouter, or a device executor.

## Direct SMS behavior

- Recipient input must be a bounded international-style phone literal: optional leading +, followed by 8–15 digits beginning with 1–9. Whitespace, option strings, URLs and hostnames are rejected.
- Message must be a non-empty string of at most 1,600 characters and may not contain NUL.
- Before invoking termux-sms-send, the module displays the exact recipient and message and requires a one-time SEND SMS <digest> response.
- The digest is domain-separated and bound to both the normalized recipient and exact UTF-8 message. Any recipient or message change produces a different challenge.
- Confirmation is implemented inside the module. No caller-supplied callback can simply return true. EOF, interruption, mismatch or unavailable Termux API causes no subprocess call.
- The command uses a fixed executable, argv list with an explicit -- option terminator before the message, shell=False, check=True and a 10-second timeout.
- A successful command exit means the Termux command completed; it is not proof of carrier delivery. Message content is not written to the log.

## WhatsApp compose behavior

send_message validates the recipient and message, percent-encodes the message as a query value, and opens https://wa.me/<digits>?text=<encoded> through termux-open-url. This only opens a prefilled compose screen. The owner must review the recipient/content and tap WhatsApp's Send control. The module does not claim that opening the compose screen sent or delivered a message.

## Regression coverage

tests/test_whatsapp_consent.py covers phone validation, challenge binding, exact confirmation, refusal, EOF/interrupt, missing Termux API, message bounds/NUL, absence of injectable confirmation callbacks, URL encoding and no-side-effect invalid input. Subprocess and input boundaries are mocked.

## Limitations

- This is a CLI-level consent challenge, not Android system credential authentication, strong owner identity or a sandbox.
- Termux still holds the permissions granted by the user; the module is not an Android runtime permission provider.
- No real SMS, WhatsApp message, network request, Termux installation or physical device was used.
- Do not expose this module to an agent/tool registry until a separate typed API, owner/session binding, durable audit/idempotency, cancellation and independent security review exist.
