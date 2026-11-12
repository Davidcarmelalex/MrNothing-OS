"""Synthetic offline tests for the M7 evidence-bundle validator."""
from __future__ import annotations

import base64
import copy
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from scripts.m7_pixel9pro_evidence import (
    ARTIFACT_SCHEMA,
    EVIDENCE_CATEGORIES,
    SCHEMA,
    canonical_payload,
    evaluate_bundle,
    load_json_strict,
)

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (ROOT / "scripts/m7_pixel9pro_evidence.py").read_text(encoding="utf-8")
COMMIT = "a" * 40


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def fixture():
    return {
        "schema": SCHEMA,
        "run_id": "M7-20261107-A1B2C3D4",
        "source_commit": COMMIT,
        "operator_id": "op_0123456789abcdef",
        "consent": {
            stage: {"approved": True, "recorded_at": "2026-11-07T00:00:00Z"}
            for stage in (
                "connect_device", "install_test_apk", "terminate_test_process", "reboot_device",
                "owner_credential_prompt", "home_role_change", "accessibility_enablement",
                "connectivity_tests", "thermal_workload",
            )
        },
        "device": {
            "manufacturer": "Google", "model": "Pixel 9 Pro", "codename": "caiman",
            "android_release": "16", "api_level": 36, "build_fingerprint_sha256": _hash("fingerprint"),
            "adb_state": "device", "emulator_marker": "absent", "bootloader_locked": True,
            "verified_boot_state": "green", "vbmeta_locked": True,
        },
        "artifact": {
            "application_id": "tech.mrnothing.os", "variant": "debug-test", "version": "0.1.0-dev",
            "apk_sha256": _hash("apk"), "signer_certificate_sha256": _hash("signer"),
            "source_commit": COMMIT, "signature_verified": True,
        },
        "strongbox": {
            "feature_advertised": True,
            "hmac": {"requested": True, "security_level": "STRONGBOX", "operation_passed": True, "alias_token_sha256": _hash("hmac-alias")},
            "aes_gcm": {"requested": True, "security_level": "STRONGBOX", "encrypt_decrypt_passed": True,
                        "tampered_tag_rejected": True, "aad_mismatch_rejected": True, "alias_token_sha256": _hash("aes-alias")},
        },
        "persistence": {
            "process_death": {"key_operations_passed": True, "aliases_unchanged": True, "security_levels_unchanged": True},
            "reboot": {"owner_approved": True, "manual_first_unlock": True, "key_operations_passed": True,
                       "aliases_unchanged": True, "security_levels_unchanged": True},
        },
        "recovery": {
            "test_namespace_only": True, "production_state_untouched": True,
            "cases": {
                "marker_only_existing_generation": {"result": "RecoveryRequired", "fallback_created": False},
                "unreadable_aes_key": {"result": "Unavailable", "fallback_created": False},
                "missing_aes_alias": {"result": "RecoveryRequired", "fallback_created": False},
                "malformed_envelope": {"result": "RecoveryRequired", "fallback_created": False},
                "interrupted_record_replacement": {"result": "RecoveryRequired", "fallback_created": False},
            },
        },
        "credential_prompt": {
            "system_prompt": True, "cancellation_tested": True, "cancel_left_trust_unchanged": True,
            "success_tested": True, "success_auth_type": "DEVICE_CREDENTIAL", "no_credentials_captured": True,
        },
        "launcher": {"home_cancel_preserved_existing": True, "home_acceptance_via_system_ui": True,
                     "stock_launcher_restored_via_settings": True},
        "accessibility": {
            "talkback_enabled_via_settings": True, "spoken_labels_verified": True, "focus_order_verified": True,
            "double_tap_verified": True, "back_home_verified": True, "large_text_verified": True,
            "keyboard_focus_verified": True, "service_revoked_via_settings": True,
        },
        "connectivity": {
            "sim_test_call_two_way_audio": True, "wifi_connect_disconnect": True,
            "bluetooth_pair_connect_disconnect": True, "local_mic_speaker_test": True, "recording_used": False,
        },
        "thermal": {
            "battery_start_percent": 85, "battery_end_percent": 78, "duration_minutes": 15,
            "start_thermal_status": "NONE", "end_thermal_status": "LIGHT", "severe_warning_observed": False,
        },
        "cleanup": {
            "test_aliases_cleaned": True, "only_disposable_aliases_touched": True,
            "production_aliases_untouched": True, "private_material_absent": True,
        },
        "stop_conditions": [],
        "deviations": [],
        "evidence_manifest": [],
        "review": {
            "decision": "approved", "reviewer_id": "rev_fedcba9876543210",
            "reviewer_role": "independent-security-reviewer", "reviewed_commit": COMMIT,
            "signed_at": "2026-11-07T00:30:00Z", "signature_algorithm": "Ed25519",
            "public_key_sha256": "0" * 64, "reviewer_inspected_all_artifacts": True, "signature": "",
        },
    }


class M7EvidenceValidatorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.evidence_dir = self.root / "evidence"
        self.evidence_dir.mkdir()
        self.private_key = Ed25519PrivateKey.generate()
        self.public_key = self.private_key.public_key()
        self.public_key_path = self.root / "reviewer.pem"
        self.public_key_path.write_bytes(self.public_key.public_bytes(
            serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
        ))
        der = self.public_key.public_bytes(serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo)
        self.fingerprint = hashlib.sha256(der).hexdigest()
        self.bundle = fixture()
        self._add_evidence()
        self._sign()

    def tearDown(self):
        self.temp.cleanup()

    def _add_evidence(self):
        for index, category in enumerate(EVIDENCE_CATEGORIES, start=1):
            artifact_id = f"ev_{index:012x}"
            content = json.dumps({"schema": ARTIFACT_SCHEMA, "category": category, "redacted": True,
                                  "observations": {"result": "pass"}}, sort_keys=True).encode()
            (self.evidence_dir / f"{artifact_id}.json").write_bytes(content)
            self.bundle["evidence_manifest"].append({
                "artifact_id": artifact_id, "category": category,
                "sha256": hashlib.sha256(content).hexdigest(), "redacted": True,
            })
        self.bundle["review"]["public_key_sha256"] = self.fingerprint

    def _sign(self):
        self.bundle["review"]["signature"] = base64.b64encode(
            self.private_key.sign(canonical_payload(self.bundle))
        ).decode("ascii")

    def _evaluate(self, bundle=None, *, key=True, fingerprint=None, evidence=True):
        return evaluate_bundle(
            copy.deepcopy(self.bundle if bundle is None else bundle),
            evidence_dir=self.evidence_dir if evidence else None,
            reviewer_public_key=self.public_key_path if key else None,
            expected_reviewer_key_sha256=(fingerprint or self.fingerprint) if key else None,
        )

    def _sign_bundle(self, data):
        data["review"]["signature"] = ""
        data["review"]["signature"] = base64.b64encode(self.private_key.sign(canonical_payload(data))).decode()

    def test_complete_bundle_with_trusted_independent_signature_is_verified_not_milestone_complete(self):
        report = self._evaluate()
        self.assertEqual(report["status"], "evidence_bundle_verified_pending_supervisor")
        self.assertTrue(report["bundle_validation_passed"])
        self.assertFalse(report["m7_milestone_complete"])
        self.assertTrue(all(report["checks"].values()))

    def test_missing_trusted_key_never_verifies_bundle(self):
        report = self._evaluate(key=False)
        self.assertEqual(report["status"], "pending_independent_verification")
        self.assertFalse(report["bundle_validation_passed"])
        self.assertFalse(report["m7_milestone_complete"])
        self.assertIn("trusted_reviewer_key_not_supplied", report["blocked_reasons"])

    def test_missing_evidence_directory_never_verifies_bundle(self):
        report = self._evaluate(evidence=False)
        self.assertFalse(report["bundle_validation_passed"])
        self.assertIn("evidence_manifest_and_digests", report["checks"])

    def test_tampered_signature_blocks(self):
        data = copy.deepcopy(self.bundle)
        data["review"]["signature"] = base64.b64encode(b"x" * 64).decode()
        self.assertIn("review_signature_invalid", self._evaluate(data)["blocked_reasons"])

    def test_wrong_trusted_key_fingerprint_blocks(self):
        self.assertIn("trusted_reviewer_key_fingerprint_mismatch", self._evaluate(fingerprint="f" * 64)["blocked_reasons"])

    def test_mutating_evidence_after_review_invalidates_signature(self):
        data = copy.deepcopy(self.bundle)
        data["device"]["api_level"] = 35
        self.assertIn("review_signature_invalid", self._evaluate(data)["blocked_reasons"])

    def test_operator_cannot_self_review(self):
        data = copy.deepcopy(self.bundle)
        data["review"]["reviewer_id"] = data["operator_id"].replace("op_", "rev_")
        self._sign_bundle(data)
        self.assertIn("reviewer_must_be_independent_of_operator", self._evaluate(data)["blocked_reasons"])

    def test_same_operator_identity_with_reviewer_prefix_is_rejected(self):
        data = copy.deepcopy(self.bundle)
        data["review"]["reviewer_id"] = "rev_" + data["operator_id"][3:]
        self._sign_bundle(data)
        self.assertIn("reviewer_must_be_independent_of_operator", self._evaluate(data)["blocked_reasons"])

    def test_wrong_device_identity_blocks(self):
        data = copy.deepcopy(self.bundle); data["device"]["model"] = "Pixel 9 Pro XL"; self._sign_bundle(data)
        self.assertIn("device_identity_mismatch", self._evaluate(data)["blocked_reasons"])

    def test_unlocked_bootloader_blocks(self):
        data = copy.deepcopy(self.bundle); data["device"]["bootloader_locked"] = False; self._sign_bundle(data)
        self.assertIn("device_boot_state_not_secure", self._evaluate(data)["blocked_reasons"])

    def test_emulator_marker_blocks(self):
        data = copy.deepcopy(self.bundle); data["device"]["emulator_marker"] = "1"; self._sign_bundle(data)
        self.assertIn("emulator_or_unknown_marker", self._evaluate(data)["blocked_reasons"])

    def test_missing_owner_consent_blocks(self):
        data = copy.deepcopy(self.bundle); data["consent"]["reboot_device"]["approved"] = False; self._sign_bundle(data)
        self.assertIn("owner_consent_missing_or_declined", self._evaluate(data)["blocked_reasons"])

    def test_tee_instead_of_strongbox_blocks(self):
        data = copy.deepcopy(self.bundle); data["strongbox"]["aes_gcm"]["security_level"] = "TRUSTED_ENVIRONMENT"; self._sign_bundle(data)
        self.assertIn("strongbox_aes_gcm_gate_failed", self._evaluate(data)["blocked_reasons"])

    def test_recovery_fallback_creation_blocks(self):
        data = copy.deepcopy(self.bundle); data["recovery"]["cases"]["missing_aes_alias"]["fallback_created"] = True; self._sign_bundle(data)
        self.assertIn("marker_first_recovery_gate_failed", self._evaluate(data)["blocked_reasons"])

    def test_production_alias_mutation_blocks(self):
        data = copy.deepcopy(self.bundle); data["cleanup"]["production_aliases_untouched"] = False; self._sign_bundle(data)
        self.assertIn("alias_cleanup_or_privacy_gate_failed", self._evaluate(data)["blocked_reasons"])

    def test_spoken_talkback_is_required(self):
        data = copy.deepcopy(self.bundle); data["accessibility"]["spoken_labels_verified"] = False; self._sign_bundle(data)
        self.assertIn("spoken_accessibility_gate_failed", self._evaluate(data)["blocked_reasons"])

    def test_connectivity_recording_is_prohibited(self):
        data = copy.deepcopy(self.bundle); data["connectivity"]["recording_used"] = True; self._sign_bundle(data)
        self.assertIn("connectivity_gate_failed", self._evaluate(data)["blocked_reasons"])

    def test_thermal_threshold_is_enforced(self):
        data = copy.deepcopy(self.bundle); data["thermal"]["duration_minutes"] = 16; self._sign_bundle(data)
        with self.assertRaisesRegex(ValueError, "thermal_values_out_of_range"):
            self._evaluate(data)

    def test_wrong_android_release_format_is_rejected(self):
        data = copy.deepcopy(self.bundle); data["device"]["android_release"] = "16 build-serial"; self._sign_bundle(data)
        with self.assertRaisesRegex(ValueError, "android_release_has_invalid_format"):
            self._evaluate(data)

    def test_evidence_digest_mismatch_blocks(self):
        path = self.evidence_dir / (self.bundle["evidence_manifest"][0]["artifact_id"] + ".json")
        path.write_text("tampered", encoding="utf-8")
        self.assertIn("evidence_artifact_digest_mismatch", self._evaluate()["blocked_reasons"])

    def test_missing_evidence_file_blocks(self):
        path = self.evidence_dir / (self.bundle["evidence_manifest"][0]["artifact_id"] + ".json")
        path.unlink()
        self.assertIn("evidence_artifact_missing_or_unsafe", self._evaluate()["blocked_reasons"])

    def test_evidence_symlink_is_rejected(self):
        item = self.bundle["evidence_manifest"][0]
        path = self.evidence_dir / (item["artifact_id"] + ".json")
        original = path.read_bytes()
        path.unlink()
        target = self.root / "outside.json"
        target.write_bytes(original)
        path.symlink_to(target)
        self.assertIn("evidence_artifact_missing_or_unsafe", self._evaluate()["blocked_reasons"])

    def test_unredacted_manifest_entry_blocks(self):
        data = copy.deepcopy(self.bundle); data["evidence_manifest"][0]["redacted"] = False; self._sign_bundle(data)
        self.assertIn("evidence_artifact_not_marked_redacted", self._evaluate(data)["blocked_reasons"])

    def test_unknown_sensitive_field_is_rejected(self):
        data = copy.deepcopy(self.bundle); data["device"]["serial"] = "must-not-be-in-bundle"
        with self.assertRaisesRegex(ValueError, "unknown_fields"):
            self._evaluate(data)

    def test_raw_alias_is_rejected_by_hash_schema(self):
        data = copy.deepcopy(self.bundle); data["strongbox"]["hmac"]["alias_token_sha256"] = "owner-authority-production-alias"
        with self.assertRaisesRegex(ValueError, "must_be_sha256"):
            self._evaluate(data)

    def test_duplicate_json_keys_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "duplicate_json_key"):
            load_json_strict(b'{"schema":"one","schema":"two"}')

    def test_non_finite_json_numbers_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "non_finite"):
            load_json_strict(b'{"value":NaN}')

    def test_excessive_json_depth_is_rejected(self):
        raw = (b"[" * 40) + b"0" + (b"]" * 40)
        with self.assertRaisesRegex(ValueError, "json_depth_limit"):
            load_json_strict(raw)

    def test_source_is_offline_and_read_only(self):
        self.assertNotIn("import subprocess", SCRIPT)
        self.assertNotIn("os.system(", SCRIPT)
        self.assertNotIn("subprocess.run(", SCRIPT)
        self.assertNotIn("adb shell", SCRIPT)

    def test_cli_writes_pending_report_without_reviewer_key(self):
        bundle_path = self.root / "bundle.json"
        output = self.root / "report.json"
        bundle_path.write_text(json.dumps(self.bundle), encoding="utf-8")
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts/m7_pixel9pro_evidence.py"),
             "--bundle", str(bundle_path), "--evidence-dir", str(self.evidence_dir), "--output", str(output)],
            cwd=ROOT, capture_output=True, text=True, check=True,
        )
        report = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(report["status"], "pending_independent_verification")
        self.assertFalse(report["bundle_validation_passed"])
        self.assertIn("pending_independent_verification", result.stdout)


if __name__ == "__main__":
    unittest.main()
