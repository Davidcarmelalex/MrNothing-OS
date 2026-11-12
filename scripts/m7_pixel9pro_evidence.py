"""Offline validator for a privacy-redacted, supervised M7 evidence bundle.

This module never invokes ADB, shell, fastboot, Android settings, or a device API.
It validates an operator-prepared evidence manifest and an independent review
signature. A trusted reviewer public-key fingerprint must be supplied out of
band; a key embedded in the bundle is never trusted.
"""
from __future__ import annotations

import argparse
import base64
import copy
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

SCHEMA = "mrnothing-m7-pixel9pro-evidence-v1"
ARTIFACT_SCHEMA = "mrnothing-m7-evidence-artifact-v1"
EXPECTED_MODEL = "Pixel 9 Pro"
EXPECTED_CODENAME = "caiman"
EXPECTED_PACKAGE = "tech.mrnothing.os"
MAX_BUNDLE_BYTES = 1_048_576
MAX_JSON_DEPTH = 32
MAX_JSON_NODES = 100_000
MAX_EVIDENCE_FILE_BYTES = 5_242_880
MAX_EVIDENCE_TOTAL_BYTES = 20_971_520
MAX_EVIDENCE_FILES = 32

CONSENT_STAGES = (
    "connect_device",
    "install_test_apk",
    "terminate_test_process",
    "reboot_device",
    "owner_credential_prompt",
    "home_role_change",
    "accessibility_enablement",
    "connectivity_tests",
    "thermal_workload",
)
RECOVERY_CASES = {
    "marker_only_existing_generation": "RecoveryRequired",
    "unreadable_aes_key": "Unavailable",
    "missing_aes_alias": "RecoveryRequired",
    "malformed_envelope": "RecoveryRequired",
    "interrupted_record_replacement": "RecoveryRequired",
}
EVIDENCE_CATEGORIES = (
    "owner_consent",
    "device_identity",
    "artifact_provenance",
    "strongbox_hmac",
    "strongbox_aes_gcm",
    "process_death",
    "reboot_persistence",
    "marker_first_recovery",
    "credential_prompt",
    "launcher_recovery",
    "talkback_navigation",
    "connectivity",
    "battery_thermal",
    "alias_cleanup",
)
THERMAL_OK = {"NONE", "LIGHT", "MODERATE"}
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
TOKEN_RE = re.compile(r"^(op|rev)_[0-9a-f]{8,32}$")
RUN_RE = re.compile(r"^M7-[0-9]{8}-[0-9A-F]{8}$")
ARTIFACT_ID_RE = re.compile(r"^ev_[0-9a-f]{12,32}$")
VERSION_RE = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+(?:-[A-Za-z0-9.-]+)?$")
ANDROID_RELEASE_RE = re.compile(r"^[0-9]+(?:\.[0-9]+){0,2}$")


def _pairs_no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate_json_key")
        result[key] = value
    return result


def _reject_constant(_: str) -> None:
    raise ValueError("non_finite_json_number")


def load_json_strict(raw: bytes, *, max_bytes: int = MAX_BUNDLE_BYTES) -> Any:
    if len(raw) > max_bytes:
        raise ValueError("json_file_too_large")
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise ValueError("json_not_utf8") from exc
    if text.startswith("\ufeff"):
        raise ValueError("json_bom_not_allowed")
    try:
        value = json.loads(
            text,
            object_pairs_hook=_pairs_no_duplicates,
            parse_constant=_reject_constant,
        )
    except json.JSONDecodeError as exc:
        raise ValueError("invalid_json") from exc
    except RecursionError as exc:
        raise ValueError("json_depth_limit") from exc
    stack = [(value, 0)]
    nodes = 0
    while stack:
        node, depth = stack.pop()
        nodes += 1
        if nodes > MAX_JSON_NODES:
            raise ValueError("json_node_limit")
        if depth > MAX_JSON_DEPTH:
            raise ValueError("json_depth_limit")
        if isinstance(node, dict):
            stack.extend((child, depth + 1) for child in node.values())
        elif isinstance(node, list):
            stack.extend((child, depth + 1) for child in node)
    return value


def canonical_payload(bundle: dict[str, Any]) -> bytes:
    payload = copy.deepcopy(bundle)
    review = payload.get("review")
    if not isinstance(review, dict) or "signature" not in review:
        raise ValueError("review_signature_missing")
    del review["signature"]
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _object(value: Any, field: str, keys: set[str]) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field}_must_be_object")
    actual = set(value)
    missing = keys - actual
    unknown = actual - keys
    if missing:
        raise ValueError(f"{field}_missing_fields")
    if unknown:
        raise ValueError(f"{field}_unknown_fields")
    return value


def _bool(obj: dict[str, Any], key: str) -> bool:
    value = obj[key]
    if type(value) is not bool:
        raise ValueError(f"{key}_must_be_boolean")
    return value


def _str(obj: dict[str, Any], key: str, pattern: re.Pattern[str] | None = None) -> str:
    value = obj[key]
    if not isinstance(value, str) or not value or len(value) > 256:
        raise ValueError(f"{key}_must_be_bounded_string")
    if any(ord(ch) < 32 for ch in value):
        raise ValueError(f"{key}_contains_control_character")
    if pattern is not None and not pattern.fullmatch(value):
        raise ValueError(f"{key}_has_invalid_format")
    return value


def _timestamp(value: Any, field: str) -> bool:
    if not isinstance(value, str) or len(value) > 40:
        raise ValueError(f"{field}_must_be_utc_timestamp")
    candidate = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError as exc:
        raise ValueError(f"{field}_must_be_utc_timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise ValueError(f"{field}_must_be_utc_timestamp")
    return True


def _hash(value: Any, field: str) -> str:
    if not isinstance(value, str) or not SHA256_RE.fullmatch(value):
        raise ValueError(f"{field}_must_be_sha256")
    return value


def _commit(value: Any, field: str) -> str:
    if not isinstance(value, str) or not COMMIT_RE.fullmatch(value):
        raise ValueError(f"{field}_must_be_git_sha1")
    return value


def _all_true(obj: dict[str, Any], keys: tuple[str, ...]) -> bool:
    return all(_bool(obj, key) for key in keys)


def _load_evidence_manifest(bundle: dict[str, Any], evidence_dir: Path | None) -> tuple[bool, list[str]]:
    manifest = bundle["evidence_manifest"]
    if not isinstance(manifest, list) or len(manifest) != len(EVIDENCE_CATEGORIES):
        raise ValueError("evidence_manifest_must_contain_all_categories")
    seen_ids: set[str] = set()
    seen_categories: set[str] = set()
    total_bytes = 0
    reasons: list[str] = []
    for item in manifest:
        item = _object(item, "evidence_manifest_item", {"artifact_id", "category", "sha256", "redacted"})
        artifact_id = _str(item, "artifact_id", ARTIFACT_ID_RE)
        category = _str(item, "category")
        _hash(item["sha256"], "evidence_sha256")
        redacted = _bool(item, "redacted")
        if artifact_id in seen_ids or category in seen_categories:
            raise ValueError("evidence_manifest_duplicate_entry")
        if category not in EVIDENCE_CATEGORIES:
            raise ValueError("evidence_manifest_unknown_category")
        if not redacted:
            reasons.append("evidence_artifact_not_marked_redacted")
        seen_ids.add(artifact_id)
        seen_categories.add(category)
        if evidence_dir is not None:
            root = evidence_dir.resolve(strict=True)
            if not root.is_dir() or evidence_dir.is_symlink():
                raise ValueError("evidence_directory_invalid")
            path = root / f"{artifact_id}.json"
            if path.is_symlink() or not path.is_file():
                reasons.append("evidence_artifact_missing_or_unsafe")
                continue
            size = path.stat().st_size
            total_bytes += size
            if size > MAX_EVIDENCE_FILE_BYTES or total_bytes > MAX_EVIDENCE_TOTAL_BYTES:
                raise ValueError("evidence_artifact_size_limit")
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            if digest != item["sha256"]:
                reasons.append("evidence_artifact_digest_mismatch")
    if seen_categories != set(EVIDENCE_CATEGORIES):
        raise ValueError("evidence_manifest_category_set_incomplete")
    if len(manifest) > MAX_EVIDENCE_FILES:
        raise ValueError("too_many_evidence_artifacts")
    return evidence_dir is not None and not reasons, reasons


def _review_signature(
    bundle: dict[str, Any],
    public_key_path: Path | None,
    expected_fingerprint: str | None,
    source_commit: str,
    operator_id: str,
) -> tuple[bool, list[str]]:
    review = _object(
        bundle["review"],
        "review",
        {
            "decision", "reviewer_id", "reviewer_role", "reviewed_commit", "signed_at",
            "signature_algorithm", "public_key_sha256", "reviewer_inspected_all_artifacts", "signature",
        },
    )
    reviewer_id = _str(review, "reviewer_id", TOKEN_RE)
    if not reviewer_id.startswith("rev_"):
        raise ValueError("reviewer_id_must_be_reviewer_token")
    if reviewer_id[4:] == operator_id[3:]:
        return False, ["reviewer_must_be_independent_of_operator"]
    if _str(review, "reviewer_role") != "independent-security-reviewer":
        return False, ["reviewer_role_not_independent_security"]
    if _str(review, "decision") != "approved":
        return False, ["independent_review_not_approved"]
    if _commit(review["reviewed_commit"], "reviewed_commit") != source_commit:
        return False, ["reviewed_commit_mismatch"]
    _timestamp(review["signed_at"], "review_signed_at")
    if _str(review, "signature_algorithm") != "Ed25519":
        raise ValueError("review_signature_algorithm_must_be_ed25519")
    _hash(review["public_key_sha256"], "review_public_key_sha256")
    if not _bool(review, "reviewer_inspected_all_artifacts"):
        return False, ["reviewer_did_not_attest_artifact_inspection"]
    signature_text = _str(review, "signature")
    try:
        signature = base64.b64decode(signature_text, validate=True)
    except (ValueError, TypeError) as exc:
        raise ValueError("review_signature_must_be_base64") from exc
    if len(signature) != 64:
        raise ValueError("review_signature_wrong_length")
    if public_key_path is None or expected_fingerprint is None:
        return False, ["trusted_reviewer_key_not_supplied"]
    _hash(expected_fingerprint, "expected_reviewer_key_sha256")
    try:
        if public_key_path.is_symlink() or public_key_path.stat().st_size > 16_384:
            raise ValueError("reviewer_public_key_file_unsafe")
        key = serialization.load_pem_public_key(public_key_path.read_bytes())
    except (OSError, ValueError) as exc:
        raise ValueError("reviewer_public_key_invalid") from exc
    if not isinstance(key, Ed25519PublicKey):
        raise ValueError("reviewer_public_key_must_be_ed25519")
    der = key.public_bytes(serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo)
    fingerprint = hashlib.sha256(der).hexdigest()
    if fingerprint != expected_fingerprint or fingerprint != review["public_key_sha256"]:
        return False, ["trusted_reviewer_key_fingerprint_mismatch"]
    try:
        key.verify(signature, canonical_payload(bundle))
    except InvalidSignature:
        return False, ["review_signature_invalid"]
    return True, []


def evaluate_bundle(
    bundle: dict[str, Any],
    *,
    evidence_dir: Path | None = None,
    reviewer_public_key: Path | None = None,
    expected_reviewer_key_sha256: str | None = None,
) -> dict[str, Any]:
    """Validate evidence completeness, artifact hashes and trusted review.

    A complete evidence bundle is verified only when all artifact digests match
    and an Ed25519 signature verifies against a separately supplied trusted key
    whose SHA-256 fingerprint also matches the independently supplied pin.
    """
    root_keys = {
        "schema", "run_id", "source_commit", "operator_id", "consent", "device", "artifact",
        "strongbox", "persistence", "recovery", "credential_prompt", "launcher", "accessibility",
        "connectivity", "thermal", "cleanup", "stop_conditions", "deviations", "evidence_manifest", "review",
    }
    bundle = _object(bundle, "bundle", root_keys)
    if _str(bundle, "schema") != SCHEMA:
        raise ValueError("unsupported_evidence_schema")
    if not RUN_RE.fullmatch(_str(bundle, "run_id")):
        raise ValueError("run_id_has_invalid_format")
    source_commit = _commit(bundle["source_commit"], "source_commit")
    operator_id = _str(bundle, "operator_id", TOKEN_RE)
    if not operator_id.startswith("op_"):
        raise ValueError("operator_id_must_be_operator_token")

    checks: dict[str, bool] = {}
    reasons: list[str] = []

    consent = _object(bundle["consent"], "consent", set(CONSENT_STAGES))
    consent_ok = True
    for stage in CONSENT_STAGES:
        record = _object(consent[stage], f"consent_{stage}", {"approved", "recorded_at"})
        consent_ok = _bool(record, "approved") and consent_ok
        _timestamp(record["recorded_at"], f"consent_{stage}_recorded_at")
    checks["owner_approved_every_stage"] = consent_ok
    if not consent_ok:
        reasons.append("owner_consent_missing_or_declined")

    device = _object(
        bundle["device"], "device",
        {"manufacturer", "model", "codename", "android_release", "api_level", "build_fingerprint_sha256",
         "adb_state", "emulator_marker", "bootloader_locked", "verified_boot_state", "vbmeta_locked"},
    )
    identity_ok = (
        _str(device, "manufacturer") == "Google"
        and _str(device, "model") == EXPECTED_MODEL
        and _str(device, "codename") == EXPECTED_CODENAME
    )
    api = device["api_level"]
    if type(api) is not int or not 34 <= api <= 100:
        raise ValueError("device_api_level_out_of_range")
    _str(device, "android_release", ANDROID_RELEASE_RE)
    _hash(device["build_fingerprint_sha256"], "build_fingerprint_sha256")
    boot_ok = (
        _bool(device, "bootloader_locked")
        and _str(device, "verified_boot_state") == "green"
        and _bool(device, "vbmeta_locked")
        and _str(device, "adb_state") == "device"
    )
    emulator_ok = _str(device, "emulator_marker") in {"absent", "0"}
    checks["exact_pixel_9_pro_identity"] = identity_ok
    checks["locked_green_verified_boot"] = boot_ok
    checks["not_marked_as_emulator"] = emulator_ok
    checks["pixel_9_api_baseline"] = api >= 34
    if not identity_ok:
        reasons.append("device_identity_mismatch")
    if not boot_ok:
        reasons.append("device_boot_state_not_secure")
    if not emulator_ok:
        reasons.append("emulator_or_unknown_marker")

    artifact = _object(
        bundle["artifact"], "artifact",
        {"application_id", "variant", "version", "apk_sha256", "signer_certificate_sha256", "source_commit", "signature_verified"},
    )
    artifact_ok = (
        _str(artifact, "application_id") == EXPECTED_PACKAGE
        and _str(artifact, "variant") == "debug-test"
        and bool(VERSION_RE.fullmatch(_str(artifact, "version")))
        and _hash(artifact["apk_sha256"], "apk_sha256") is not None
        and _hash(artifact["signer_certificate_sha256"], "signer_certificate_sha256") is not None
        and _commit(artifact["source_commit"], "artifact_source_commit") == source_commit
        and _bool(artifact, "signature_verified")
    )
    checks["test_artifact_provenance"] = artifact_ok
    if not artifact_ok:
        reasons.append("test_artifact_provenance_invalid")

    strongbox = _object(bundle["strongbox"], "strongbox", {"feature_advertised", "hmac", "aes_gcm"})
    feature_ok = _bool(strongbox, "feature_advertised")
    hmac = _object(strongbox["hmac"], "strongbox_hmac", {"requested", "security_level", "operation_passed", "alias_token_sha256"})
    aes = _object(strongbox["aes_gcm"], "strongbox_aes_gcm", {"requested", "security_level", "encrypt_decrypt_passed", "tampered_tag_rejected", "aad_mismatch_rejected", "alias_token_sha256"})
    hmac_ok = feature_ok and _bool(hmac, "requested") and _str(hmac, "security_level") == "STRONGBOX" and _bool(hmac, "operation_passed")
    aes_ok = feature_ok and _bool(aes, "requested") and _str(aes, "security_level") == "STRONGBOX" and _bool(aes, "encrypt_decrypt_passed") and _bool(aes, "tampered_tag_rejected") and _bool(aes, "aad_mismatch_rejected")
    _hash(hmac["alias_token_sha256"], "hmac_alias_token_sha256")
    _hash(aes["alias_token_sha256"], "aes_alias_token_sha256")
    checks["hmac_key_is_strongbox_backed"] = hmac_ok
    checks["aes_gcm_key_is_strongbox_backed"] = aes_ok
    if not hmac_ok:
        reasons.append("strongbox_hmac_gate_failed")
    if not aes_ok:
        reasons.append("strongbox_aes_gcm_gate_failed")

    persistence = _object(bundle["persistence"], "persistence", {"process_death", "reboot"})
    process = _object(persistence["process_death"], "process_death", {"key_operations_passed", "aliases_unchanged", "security_levels_unchanged"})
    reboot = _object(persistence["reboot"], "reboot", {"owner_approved", "manual_first_unlock", "key_operations_passed", "aliases_unchanged", "security_levels_unchanged"})
    process_ok = _all_true(process, ("key_operations_passed", "aliases_unchanged", "security_levels_unchanged"))
    reboot_ok = _all_true(reboot, ("owner_approved", "manual_first_unlock", "key_operations_passed", "aliases_unchanged", "security_levels_unchanged"))
    checks["process_death_persistence"] = process_ok
    checks["owner_approved_reboot_persistence"] = reboot_ok
    if not process_ok:
        reasons.append("process_death_persistence_failed")
    if not reboot_ok:
        reasons.append("reboot_persistence_failed")

    recovery = _object(bundle["recovery"], "recovery", {"test_namespace_only", "production_state_untouched", "cases"})
    cases = _object(recovery["cases"], "recovery_cases", set(RECOVERY_CASES))
    recovery_ok = _bool(recovery, "test_namespace_only") and _bool(recovery, "production_state_untouched")
    for name, expected_result in RECOVERY_CASES.items():
        case = _object(cases[name], f"recovery_{name}", {"result", "fallback_created"})
        recovery_ok = (_str(case, "result") == expected_result and not _bool(case, "fallback_created")) and recovery_ok
    checks["marker_first_fail_closed_recovery"] = recovery_ok
    if not recovery_ok:
        reasons.append("marker_first_recovery_gate_failed")

    credential = _object(bundle["credential_prompt"], "credential_prompt", {"system_prompt", "cancellation_tested", "cancel_left_trust_unchanged", "success_tested", "success_auth_type", "no_credentials_captured"})
    credential_ok = _all_true(credential, ("system_prompt", "cancellation_tested", "cancel_left_trust_unchanged", "success_tested", "no_credentials_captured")) and _str(credential, "success_auth_type") == "DEVICE_CREDENTIAL"
    checks["platform_credential_prompt"] = credential_ok
    if not credential_ok:
        reasons.append("credential_prompt_gate_failed")

    launcher = _object(bundle["launcher"], "launcher", {"home_cancel_preserved_existing", "home_acceptance_via_system_ui", "stock_launcher_restored_via_settings"})
    launcher_ok = _all_true(launcher, ("home_cancel_preserved_existing", "home_acceptance_via_system_ui", "stock_launcher_restored_via_settings"))
    checks["launcher_and_stock_recovery"] = launcher_ok
    if not launcher_ok:
        reasons.append("launcher_recovery_gate_failed")

    accessibility = _object(bundle["accessibility"], "accessibility", {"talkback_enabled_via_settings", "spoken_labels_verified", "focus_order_verified", "double_tap_verified", "back_home_verified", "large_text_verified", "keyboard_focus_verified", "service_revoked_via_settings"})
    accessibility_ok = _all_true(accessibility, tuple(accessibility))
    checks["spoken_talkback_accessibility"] = accessibility_ok
    if not accessibility_ok:
        reasons.append("spoken_accessibility_gate_failed")

    connectivity = _object(bundle["connectivity"], "connectivity", {"sim_test_call_two_way_audio", "wifi_connect_disconnect", "bluetooth_pair_connect_disconnect", "local_mic_speaker_test", "recording_used"})
    connectivity_ok = _all_true(connectivity, ("sim_test_call_two_way_audio", "wifi_connect_disconnect", "bluetooth_pair_connect_disconnect", "local_mic_speaker_test")) and not _bool(connectivity, "recording_used")
    checks["connectivity_and_local_audio"] = connectivity_ok
    if not connectivity_ok:
        reasons.append("connectivity_gate_failed")

    thermal = _object(bundle["thermal"], "thermal", {"battery_start_percent", "battery_end_percent", "duration_minutes", "start_thermal_status", "end_thermal_status", "severe_warning_observed"})
    start_battery, end_battery, duration = thermal["battery_start_percent"], thermal["battery_end_percent"], thermal["duration_minutes"]
    if any(type(value) is not int for value in (start_battery, end_battery, duration)):
        raise ValueError("thermal_numeric_fields_must_be_integers")
    if not (0 <= end_battery <= 100 and 60 <= start_battery <= 100 and duration == 15):
        raise ValueError("thermal_values_out_of_range")
    thermal_ok = _str(thermal, "start_thermal_status") in THERMAL_OK and _str(thermal, "end_thermal_status") in THERMAL_OK and not _bool(thermal, "severe_warning_observed")
    checks["battery_and_thermal"] = thermal_ok
    if not thermal_ok:
        reasons.append("thermal_gate_failed")

    cleanup = _object(bundle["cleanup"], "cleanup", {"test_aliases_cleaned", "only_disposable_aliases_touched", "production_aliases_untouched", "private_material_absent"})
    cleanup_ok = _all_true(cleanup, tuple(cleanup))
    checks["disposable_alias_cleanup_and_privacy"] = cleanup_ok
    if not cleanup_ok:
        reasons.append("alias_cleanup_or_privacy_gate_failed")

    stop_conditions = bundle["stop_conditions"]
    deviations = bundle["deviations"]
    if not isinstance(stop_conditions, list) or not all(isinstance(x, str) and len(x) <= 64 for x in stop_conditions):
        raise ValueError("stop_conditions_must_be_bounded_string_list")
    if not isinstance(deviations, list) or not all(isinstance(x, str) and len(x) <= 64 for x in deviations):
        raise ValueError("deviations_must_be_bounded_string_list")
    checks["no_stop_conditions_or_deviations"] = not stop_conditions and not deviations
    if stop_conditions or deviations:
        reasons.append("stop_condition_or_deviation_present")

    evidence_ok, evidence_reasons = _load_evidence_manifest(bundle, evidence_dir)
    checks["evidence_manifest_and_digests"] = evidence_ok
    reasons.extend(evidence_reasons)

    review_ok, review_reasons = _review_signature(
        bundle, reviewer_public_key, expected_reviewer_key_sha256, source_commit, operator_id
    )
    checks["trusted_independent_reviewer_signature"] = review_ok
    reasons.extend(review_reasons)

    reasons = list(dict.fromkeys(reasons))
    bundle_validated = all(checks.values())
    if bundle_validated:
        status = "evidence_bundle_verified_pending_supervisor"
    elif any(reason not in {"trusted_reviewer_key_not_supplied"} for reason in reasons):
        status = "blocked"
    else:
        status = "pending_independent_verification"
    return {
        "schema": "mrnothing-m7-pixel9pro-evidence-result-v1",
        "status": status,
        "bundle_validation_passed": bundle_validated,
        "m7_milestone_complete": False,
        "source_commit": source_commit,
        "checks": checks,
        "blocked_reasons": reasons,
        "note": (
            "This validator checks schema, artifact digests and a trusted Ed25519 review signature. "
            "The reviewer key fingerprint must be pinned out of band. It does not prove the truth of "
            "operator observations or inspect the semantic content of attachments. A human supervisor "
            "must inspect the evidence and separately decide whether M7 is complete."
        ),
    }


def _cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", required=True, type=Path, help="privacy-redacted M7 evidence JSON")
    parser.add_argument("--evidence-dir", required=True, type=Path, help="directory containing ev_<token>.json evidence artifacts")
    parser.add_argument("--reviewer-public-key", type=Path, help="trusted independent reviewer Ed25519 PEM public key")
    parser.add_argument("--expected-reviewer-key-sha256", help="out-of-band pinned SHA-256 fingerprint of reviewer SPKI DER")
    parser.add_argument("--output", required=True, type=Path, help="redacted validation report path")
    args = parser.parse_args(argv)
    if bool(args.reviewer_public_key) != bool(args.expected_reviewer_key_sha256):
        print("M7 evidence rejected: reviewer_key_and_fingerprint_must_be_supplied_together", file=sys.stderr)
        return 2
    try:
        if args.bundle.is_symlink() or not args.bundle.is_file():
            raise ValueError("bundle_path_unsafe_or_missing")
        if args.output.is_symlink():
            raise ValueError("output_path_symlink_not_allowed")
        if args.bundle.stat().st_size > MAX_BUNDLE_BYTES:
            raise ValueError("json_file_too_large")
        raw = args.bundle.read_bytes()
        bundle = load_json_strict(raw)
        if not isinstance(bundle, dict):
            raise ValueError("bundle_must_be_object")
        report = evaluate_bundle(
            bundle,
            evidence_dir=args.evidence_dir,
            reviewer_public_key=args.reviewer_public_key,
            expected_reviewer_key_sha256=args.expected_reviewer_key_sha256,
        )
        args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    except (OSError, ValueError) as exc:
        print(f"M7 evidence rejected: {exc}", file=sys.stderr)
        return 2
    print(f"M7 evidence validation: {report['status']}")
    return 0 if report["bundle_validation_passed"] or report["status"] == "pending_independent_verification" else 1


if __name__ == "__main__":
    raise SystemExit(_cli())
