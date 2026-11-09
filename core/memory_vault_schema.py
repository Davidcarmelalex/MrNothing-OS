"""SEC-023A: offline canonical envelope and AAD preflight, NOT encryption.

No Android Keystore access, IPC, persistence, owner authentication, nonce
generation, or AEAD tag verification occurs in this module. Inputs are
synthetic/untrusted; a trusted native vault must enforce the real gates.
"""
import base64
import hmac
import json
import re

FORMAT_VERSION = 1
MAX_ENVELOPE_BYTES = 100_000
MAX_CIPHERTEXT_BYTES = 65_536
MAX_RETENTION_SECONDS = 90 * 24 * 60 * 60
MIN_UNIX_TIME = 1_577_836_800  # 2020-01-01 UTC
MAX_UNIX_TIME = 4_102_444_800  # 2100-01-01 UTC
MAX_GENERATION = (1 << 63) - 1
MAX_KEY_VERSION = (1 << 31) - 1
FIELDS = frozenset({
    "format_version", "vault_id", "record_id", "generation",
    "created_at", "expires_at", "key_version", "nonce", "ciphertext", "tag",
})
_B64URL = re.compile(r"[A-Za-z0-9_-]+\Z", re.ASCII)
_OWNER_ID = re.compile(r"[A-Za-z0-9_.:-]{1,128}\Z", re.ASCII)
_SHA256 = re.compile(r"[0-9a-f]{64}\Z", re.ASCII)


class EnvelopeError(ValueError):
    """Untrusted envelope or context fails the strict offline schema."""


def _reject_constant(value):
    raise EnvelopeError("nonfinite JSON number")


def _unique_object(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise EnvelopeError("duplicate JSON key")
        obj[key] = value
    return obj


def _canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def _unsigned(value, field, lower, upper):
    if type(value) is not int or not lower <= value <= upper:
        raise EnvelopeError("invalid " + field)


def _base64url(value, field, minimum, maximum):
    if type(value) is not str or not _B64URL.fullmatch(value):
        raise EnvelopeError("invalid " + field)
    try:
        decoded = base64.b64decode(value + "=" * (-len(value) % 4),
                                   altchars=b"-_", validate=True)
    except (ValueError, base64.binascii.Error) as exc:
        raise EnvelopeError("invalid " + field) from exc
    if not minimum <= len(decoded) <= maximum:
        raise EnvelopeError("invalid " + field + " length")
    if base64.urlsafe_b64encode(decoded).decode("ascii").rstrip("=") != value:
        raise EnvelopeError("noncanonical " + field)
    return decoded


def _validate(envelope):
    if type(envelope) is not dict or envelope.keys() != FIELDS:
        raise EnvelopeError("missing or unknown envelope fields")
    _unsigned(envelope["format_version"], "format_version", 1, 1)
    _unsigned(envelope["generation"], "generation", 1, MAX_GENERATION)
    _unsigned(envelope["key_version"], "key_version", 1, MAX_KEY_VERSION)
    _unsigned(envelope["created_at"], "created_at", MIN_UNIX_TIME, MAX_UNIX_TIME)
    _unsigned(envelope["expires_at"], "expires_at", MIN_UNIX_TIME, MAX_UNIX_TIME)
    if not 0 < envelope["expires_at"] - envelope["created_at"] <= MAX_RETENTION_SECONDS:
        raise EnvelopeError("invalid retention window")
    _base64url(envelope["vault_id"], "vault_id", 16, 16)
    _base64url(envelope["record_id"], "record_id", 16, 16)
    _base64url(envelope["nonce"], "nonce", 12, 12)
    _base64url(envelope["tag"], "tag", 16, 16)
    _base64url(envelope["ciphertext"], "ciphertext", 1, MAX_CIPHERTEXT_BYTES)


def encode_envelope(envelope):
    """Produce a strict canonical byte representation of a validated fixture."""
    _validate(envelope)
    raw = _canonical(envelope)
    if len(raw) > MAX_ENVELOPE_BYTES:
        raise EnvelopeError("oversized envelope")
    return raw


def parse_envelope(raw):
    """Reject noncanonical JSON, duplicate keys, oversized/invalid inputs."""
    if type(raw) is not bytes or not 0 < len(raw) <= MAX_ENVELOPE_BYTES:
        raise EnvelopeError("invalid envelope byte size/type")
    try:
        parsed = json.loads(raw.decode("utf-8", "strict"),
                            object_pairs_hook=_unique_object,
                            parse_constant=_reject_constant)
    except (UnicodeError, json.JSONDecodeError, RecursionError) as exc:
        raise EnvelopeError("invalid JSON encoding") from exc
    _validate(parsed)
    if _canonical(parsed) != raw:
        raise EnvelopeError("noncanonical envelope serialization")
    return parsed


def canonical_aad(envelope, *, owner_profile_id, application_identity):
    """AAD bytes for future native AES-GCM; not an authentication check."""
    _validate(envelope)
    if type(owner_profile_id) is not str or not _OWNER_ID.fullmatch(owner_profile_id):
        raise EnvelopeError("invalid trusted owner profile")
    if type(application_identity) is not str or not _SHA256.fullmatch(application_identity):
        raise EnvelopeError("invalid trusted application signing digest")
    return _canonical({
        "application_identity": application_identity,
        "format_version": envelope["format_version"],
        "generation": envelope["generation"],
        "key_version": envelope["key_version"],
        "owner_profile_id": owner_profile_id,
        "record_id": envelope["record_id"],
        "vault_id": envelope["vault_id"],
    })


def preflight_record(envelope, *, expected_vault_id, expected_record_id,
                     last_accepted_generation, seen_key_nonces, trusted_now,
                     owner_profile_id, application_identity):
    """Pure offline rejection checks; NEVER treats a tag as authenticated.

    seen_key_nonces must be a trusted per-key ledger of (key_version, nonce)
    pairs. Caller must verify AES-GCM and commit ledger atomically separately.
    """
    _validate(envelope)
    for expected, field in ((expected_vault_id, "vault_id"),
                            (expected_record_id, "record_id")):
        _base64url(expected, "expected_" + field, 16, 16)
        if not hmac.compare_digest(expected, envelope[field]):
            raise EnvelopeError("record identity mismatch")
    _unsigned(trusted_now, "trusted_now", MIN_UNIX_TIME, MAX_UNIX_TIME)
    if envelope["expires_at"] <= trusted_now:
        raise EnvelopeError("expired record")
    if envelope["created_at"] > trusted_now + 300:
        raise EnvelopeError("future-dated record")
    _unsigned(last_accepted_generation, "last_accepted_generation", 0, MAX_GENERATION)
    if envelope["generation"] <= last_accepted_generation:
        raise EnvelopeError("stale or replayed generation")
    if type(seen_key_nonces) not in (set, frozenset):
        raise EnvelopeError("invalid trusted nonce ledger")
    if (envelope["key_version"], envelope["nonce"]) in seen_key_nonces:
        raise EnvelopeError("reused nonce for encryption key")
    return canonical_aad(envelope, owner_profile_id=owner_profile_id,
                         application_identity=application_identity)
